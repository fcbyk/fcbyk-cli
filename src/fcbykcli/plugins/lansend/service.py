import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class LansendConfig:
    shared_directory: str | None = None
    upload_password: str | None = None
    un_download: bool = False
    un_upload: bool = False
    chat_enabled: bool = False


class LansendService:
    """局域网文件传输服务类。"""

    def __init__(self, config: LansendConfig):
        self.config = config

    # -------------------- 基础工具方法 --------------------
    @staticmethod
    def safe_filename(filename: str) -> str:
        """清理文件名中的非法字符。"""
        return re.sub(r"[^\w\s\u4e00-\u9fff\-\.]", "", filename)

    @staticmethod
    def is_image_file(filename: str) -> bool:
        """判断是否为图片文件。"""
        image_extensions = {
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".tif"
        }
        ext = os.path.splitext(filename)[1].lower()
        return ext in image_extensions

    @staticmethod
    def is_video_file(filename: str) -> bool:
        """判断是否为视频文件。"""
        video_extensions = {
            ".mp4", ".webm", ".ogg", ".mov", ".mkv", ".avi", ".m4v"
        }
        ext = os.path.splitext(filename)[1].lower()
        return ext in video_extensions

    @staticmethod
    def format_size(num_bytes: int | None) -> str:
        """格式化文件大小为人类可读的格式。"""
        if num_bytes is None:
            return "unknown size"
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(num_bytes)
        for unit in units:
            if size < 1024 or unit == units[-1]:
                return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} {unit}"
            size /= 1024
        return f"{size:.2f} {units[-1]}"

    @staticmethod
    def get_path_parts(current_path: str) -> list[dict[str, str]]:
        """把相对路径拆成面包屑。

        注意：这里必须统一使用 URL 风格的 "/" 分隔符。
        在 Windows 上如果用 os.path.join，会生成 "\\"，从而导致前端面包屑拼接/跳转异常。
        """
        parts: list[dict[str, str]] = []
        if current_path:
            path_parts = current_path.split("/")
            current = ""
            for part in path_parts:
                if part:
                    # 强制使用 "/" 作为分隔符，避免 Windows 反斜杠污染 API 返回
                    current = f"{current}/{part}" if current else part
                    parts.append({"name": part, "path": current})
        return parts

    def log_upload(
        self,
        ip: str,
        file_count: int,
        status: str,
        rel_path: str = "",
        file_size: int | None = None,
    ) -> None:
        """记录上传日志。"""
        import sys
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        path_str = f"/{rel_path}" if rel_path else "/"
        size_str = self.format_size(file_size) if file_size is not None else "unknown size"
        log_msg = f" [{ts}] {ip} upload {file_count} file(s), status: {status}, path: {path_str}, size: {size_str}\n"
        sys.stderr.write(log_msg)
        sys.stderr.flush()

    # -------------------- 业务逻辑 --------------------
    def ensure_shared_directory(self) -> str:
        if not self.config.shared_directory:
            raise ValueError("shared directory not set")
        return self.config.shared_directory

    def abs_target_dir(self, rel_path: str) -> str:
        base = self.ensure_shared_directory()
        rel_path = (rel_path or "").strip("/")
        target_dir = os.path.abspath(os.path.join(base, rel_path))
        base_abs = os.path.abspath(base)
        # 安全检查：确保目标目录在共享目录内，防止路径遍历攻击
        if not target_dir.startswith(base_abs):
            raise PermissionError("invalid path")
        return target_dir

    def get_file_tree(self, base_path: str, relative_path: str = "") -> list[dict[str, Any]]:
        """获取文件树结构。"""
        current_path = os.path.join(base_path, relative_path) if relative_path else base_path
        items: list[dict[str, Any]] = []

        if not os.path.exists(current_path) or not os.path.isdir(current_path):
            return items

        for name in os.listdir(current_path):
            full_path = os.path.join(current_path, name)
            item_path = os.path.join(relative_path, name) if relative_path else name

            item: dict[str, Any] = {
                "name": name,
                "path": item_path.replace("\\", "/"),  # 统一使用 "/" 分隔符
                "is_dir": os.path.isdir(full_path),
            }

            if item["is_dir"]:
                item["children"] = self.get_file_tree(base_path, item_path)

            items.append(item)

        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return items

    def get_directory_listing(self, relative_path: str = "") -> dict[str, Any]:
        """获取目录列表信息。"""
        base = self.ensure_shared_directory()
        relative_path = (relative_path or "").strip("/")
        current_path = os.path.join(base, relative_path) if relative_path else base

        if not os.path.exists(current_path) or not os.path.isdir(current_path):
            raise FileNotFoundError("Directory not found")

        items: list[dict[str, Any]] = []
        for name in os.listdir(current_path):
            full_path = os.path.join(current_path, name)
            item_path = os.path.join(relative_path, name) if relative_path else name
            items.append(
                {
                    "name": name,
                    "path": item_path.replace("\\", "/"),  # 统一使用 "/" 分隔符
                    "is_dir": os.path.isdir(full_path),
                }
            )
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

        # 处理磁盘根目录情况 (如 Windows 的 D:\ 或 Linux 的 /)，os.path.basename 会返回空
        share_name = os.path.basename(base) or base.rstrip(os.sep) or base
        return {
            "share_name": share_name,
            "relative_path": relative_path,
            "path_parts": self.get_path_parts(relative_path),
            "items": items,
            "require_password": bool(self.config.upload_password),
        }

    def resolve_file_path(self, filename: str) -> str:
        base = self.ensure_shared_directory()
        normalized_path = (filename or "").replace("/", os.sep)
        file_path = os.path.abspath(os.path.join(base, normalized_path))
        # 安全检查：确保文件路径在共享目录内，防止路径遍历攻击
        if not file_path.startswith(os.path.abspath(base)):
            raise PermissionError("Invalid path")
        return file_path

    def read_file_content(self, relative_path: str) -> dict[str, Any]:
        """读取文件内容（文本/图片/视频/二进制）。

        规则：
        - 图片：直接返回 is_image，不读取内容
        - 视频：直接返回 is_video，不读取内容（前端用 /api/preview 做 Range 播放）
        - 文本：最多预览 2MB，超过则按二进制处理（避免前端/后端卡死）
        - 其它：按二进制处理
        """
        file_path = self.resolve_file_path(relative_path)

        if not os.path.exists(file_path) or os.path.isdir(file_path):
            raise FileNotFoundError("File not found")

        raw_name = os.path.basename(relative_path)
        lower_name = raw_name.lower()

        # 1) 图片：不读取内容
        if self.is_image_file(lower_name):
            return {
                "is_image": True,
                "path": relative_path,
                "name": raw_name,
            }

        # 2) 视频：不读取内容（由 /api/preview 支持 Range 播放）
        if self.is_video_file(lower_name):
            return {
                "is_video": True,
                "path": relative_path,
                "name": raw_name,
            }

        # 3) 文本：最多 2MB
        max_preview_bytes = 2 * 1024 * 1024
        try:
            file_size = os.path.getsize(file_path)
            if file_size > max_preview_bytes:
                return {
                    "is_binary": True,
                    "path": relative_path,
                    "name": raw_name,
                    "error": "文件过大，超过 2MB，建议在浏览器打开",
                }

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read(max_preview_bytes + 1)

            if len(content) > max_preview_bytes:
                return {
                    "is_binary": True,
                    "path": relative_path,
                    "name": raw_name,
                    "error": "文件过大，超过 2MB，建议在浏览器打开",
                }

            return {
                "content": content,
                "path": relative_path,
                "name": raw_name,
            }

        except UnicodeDecodeError:
            return {
                "is_binary": True,
                "path": relative_path,
                "name": raw_name,
                "error": "二进制文件无法预览，建议在浏览器打开",
            }

    def pick_upload_password(self, flag_password: bool, un_upload: bool, click_module) -> str | None:
        """根据参数决定是否提示输入上传密码（保持旧行为）。"""
        if flag_password and not un_upload:
            pw = click_module.prompt(
                "Upload password (press Enter to use default: 123456)",
                hide_input=True,
                default="123456",
                show_default=False,
            )
            pw = pw if pw else "123456"
            return pw
        return None

