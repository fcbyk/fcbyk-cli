import time
import uuid
import queue
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class TransferUser:
    id: str
    ip: str
    name: str
    icon: str
    last_seen: float
    is_me: bool = False
    is_server: bool = False

@dataclass
class TransferRequest:
    id: str
    sender_ip: str
    receiver_ip: str
    file_name: str
    file_size: int
    file_type: str
    status: str  # 'pending', 'accepted', 'rejected', 'transferring', 'completed', 'cancelled'
    created_at: float

class TransferBuffer:
    def __init__(self, max_size_mb: int = 10):
        # 使用 Queue 实现背压：如果 receiver 读得慢，sender 的 put 会阻塞
        # 每个 chunk 大约为 1MB，maxsize=10 表示最多缓存 10MB
        self.queue = queue.Queue(maxsize=max_size_mb)
        self.is_finished = False
        self.error: Optional[str] = None

    def put(self, chunk: bytes, timeout: float = 30):
        try:
            self.queue.put(chunk, timeout=timeout)
        except queue.Full:
            raise TimeoutError("Transfer push timeout (receiver too slow)")

    def get(self, timeout: float = 30) -> Optional[bytes]:
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            if self.is_finished:
                return None
            raise TimeoutError("Transfer pull timeout (sender too slow)")

    def finish(self):
        self.is_finished = True

class TransferService:
    def __init__(self):
        self.users: Dict[str, TransferUser] = {}  # ip -> TransferUser
        self.requests: Dict[str, TransferRequest] = {}  # task_id -> TransferRequest
        self.buffers: Dict[str, TransferBuffer] = {}  # task_id -> TransferBuffer
        self.offline_threshold = 10.0  # 10秒不活跃视为离线

    # ---------------- 用户管理 ----------------
    def update_user(self, ip: str, name: str, icon: str, is_me: bool = False, is_server: bool = False):
        self.users[ip] = TransferUser(
            id=ip,  # 暂时用 IP 作为 ID
            ip=ip,
            name=name,
            icon=icon,
            last_seen=time.time(),
            is_me=is_me,
            is_server=is_server
        )

    def get_online_users(self) -> List[Dict[str, Any]]:
        now = time.time()
        online_users = []
        for ip, user in self.users.items():
            if now - user.last_seen < self.offline_threshold:
                online_users.append({
                    "id": user.id,
                    "name": user.name,
                    "icon": user.icon,
                    "ip": user.ip,
                    "isMe": user.is_me,
                    "isServer": user.is_server
                })
        return online_users

    def get_pending_request(self, ip: str, include_server: bool = False) -> Optional[Dict[str, Any]]:
        """获取发给指定 IP 的待处理请求"""
        for req in self.requests.values():
            # 匹配逻辑：IP 匹配 或者 (包含服务器请求 且 接收者是 SERVER)
            is_target = (req.receiver_ip == ip) or (include_server and req.receiver_ip == 'SERVER')
            
            if is_target and req.status == 'pending':
                sender = self.users.get(req.sender_ip)
                return {
                    "id": req.id,
                    "sender": {
                        "id": sender.id if sender else req.sender_ip,
                        "name": sender.name if sender else "Unknown",
                        "ip": req.sender_ip
                    },
                    "file": {
                        "name": req.file_name,
                        "size": req.file_size,
                        "type": req.file_type
                    }
                }
        return None

    # ---------------- 传输任务管理 ----------------
    def create_request(self, sender_ip: str, receiver_ip: str, file_info: Dict[str, Any]) -> str:
        task_id = str(uuid.uuid4())
        
        # 即使发给服务器，也初始为 pending，等待服务器端手动接受
        status = 'pending'
            
        self.requests[task_id] = TransferRequest(
            id=task_id,
            sender_ip=sender_ip,
            receiver_ip=receiver_ip,
            file_name=file_info.get('name', 'unknown'),
            file_size=file_info.get('size', 0),
            file_type=file_info.get('type', 'application/octet-stream'),
            status=status,
            created_at=time.time()
        )
        return task_id

    def respond_request(self, task_id: str, accepted: bool) -> bool:
        if task_id in self.requests:
            req = self.requests[task_id]
            req.status = 'accepted' if accepted else 'rejected'
            if accepted:
                # 无论是普通用户还是 SERVER，只要接受了，就创建缓冲区
                self.buffers[task_id] = TransferBuffer()
            return True
        return False

    def get_request_status(self, task_id: str) -> Optional[str]:
        if task_id in self.requests:
            return self.requests[task_id].status
        return None

    def push_chunk(self, task_id: str, chunk: bytes):
        if task_id in self.buffers:
            self.buffers[task_id].put(chunk)
            self.requests[task_id].status = 'transferring'

    def finish_push(self, task_id: str):
        if task_id in self.buffers:
            self.buffers[task_id].finish()
            if task_id in self.requests:
                self.requests[task_id].status = 'pushed'

    def pull_chunk(self, task_id: str) -> Optional[bytes]:
        if task_id in self.buffers:
            chunk = self.buffers[task_id].get()
            if chunk is None:
                # 传输完成
                if task_id in self.requests:
                    self.requests[task_id].status = 'completed'
                # 清理缓冲区资源，但保留请求记录供前端查询最终状态
                self.cleanup_task(task_id)
            return chunk
        return None

    def cancel_transfer(self, task_id: str, error: Optional[str] = None):
        if task_id in self.requests:
            self.requests[task_id].status = 'cancelled'
        if task_id in self.buffers:
            self.buffers[task_id].error = error
            self.cleanup_task(task_id)

    def cleanup_task(self, task_id: str):
        if task_id in self.buffers:
            del self.buffers[task_id]
        # 注意：requests 记录可以保留一段时间用于状态查询，这里简单处理直接保留
