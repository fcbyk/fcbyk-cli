"""
lansend service 层
负责纯业务逻辑：路径/文件处理、目录树、内容读取等
"""

import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class LansendConfig:
    shared_directory: Optional[str] = None
    display_name: str = "共享文件夹"
    upload_password: Optional[str] = None
    ide_mode: bool = False


class LansendService:
    def __init__(self, config: LansendConfig):
        self.config = config
        self._first_upload_log = True

    # -------------------- 基础工具 --------------------
    @staticmethod
    def safe_filename(filename: str) -> str:
        return re.sub(r"[^\w\s\u4e00-\u9fff\-\.]", "", filename)

    @staticmethod
    def is_image_file(filename: str) -> bool:
        image_extensions = {
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".tif"
        }
        ext = os.path.splitext(filename)[1].lower()
        return ext in image_extensions

    @staticmethod
    def format_size(num_bytes: Optional[int]) -> str:
        if num_bytes is None:
            return "unknown size"
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(num_bytes)
        for unit in units:
            if size < 1024 or unit == units[-1]:
                return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} {unit}"
            size /= 1024

    @staticmethod
    def get_path_parts(current_path: str) -> List[Dict[str, str]]:
        """把相对路径拆成面包屑。

        注意：这里必须统一使用 URL 风格的 "/" 分隔符。
        在 Windows 上如果用 os.path.join，会生成 "\\"，从而导致前端面包屑拼接/跳转异常。
        """
        parts: List[Dict[str, str]] = []
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
        file_size: Optional[int] = None,
    ) -> None:
        if self._first_upload_log:
            print("", flush=True)
            self._first_upload_log = False

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        path_str = f"/{rel_path}" if rel_path else "/"
        size_str = self.format_size(file_size) if file_size is not None else "unknown size"
        print(
            f"[{ts}] {ip} upload {file_count} file(s), status: {status}, path: {path_str}, size: {size_str}",
            flush=True,
        )

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
        if not target_dir.startswith(base_abs):
            raise PermissionError("invalid path")
        return target_dir

    def get_file_tree(self, base_path: str, relative_path: str = "") -> List[Dict[str, Any]]:
        current_path = os.path.join(base_path, relative_path) if relative_path else base_path
        items: List[Dict[str, Any]] = []

        if not os.path.exists(current_path) or not os.path.isdir(current_path):
            return items

        for name in os.listdir(current_path):
            full_path = os.path.join(current_path, name)
            item_path = os.path.join(relative_path, name) if relative_path else name

            item: Dict[str, Any] = {
                "name": name,
                "path": item_path.replace("\\", "/"),
                "is_dir": os.path.isdir(full_path),
            }

            if item["is_dir"]:
                item["children"] = self.get_file_tree(base_path, item_path)

            items.append(item)

        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return items

    def get_directory_listing(self, relative_path: str = "") -> Dict[str, Any]:
        base = self.ensure_shared_directory()
        relative_path = (relative_path or "").strip("/")
        current_path = os.path.join(base, relative_path) if relative_path else base

        if not os.path.exists(current_path) or not os.path.isdir(current_path):
            raise FileNotFoundError("Directory not found")

        items: List[Dict[str, Any]] = []
        for name in os.listdir(current_path):
            full_path = os.path.join(current_path, name)
            item_path = os.path.join(relative_path, name) if relative_path else name
            items.append(
                {
                    "name": name,
                    "path": item_path.replace("\\", "/"),
                    "is_dir": os.path.isdir(full_path),
                }
            )
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

        share_name = os.path.basename(base)
        return {
            "display_name": self.config.display_name,
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
        if not file_path.startswith(os.path.abspath(base)):
            raise PermissionError("Invalid path")
        return file_path

    def read_file_content(self, relative_path: str) -> Dict[str, Any]:
        file_path = self.resolve_file_path(relative_path)

        if not os.path.exists(file_path) or os.path.isdir(file_path):
            raise FileNotFoundError("File not found")

        if self.is_image_file(file_path):
            return {
                "is_image": True,
                "path": relative_path,
                "name": os.path.basename(relative_path),
            }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "content": content,
                "path": relative_path,
                "name": os.path.basename(relative_path),
                "is_image": False,
            }
        except UnicodeDecodeError:
            return {
                "is_binary": True,
                "path": relative_path,
                "name": os.path.basename(relative_path),
                "error": "Binary file cannot be displayed",
            }

    def pick_upload_password(self, flag_password: bool, ide: bool, click_module) -> Optional[str]:
        """根据参数决定是否提示输入上传密码（保持旧行为）。"""
        if flag_password and not ide:
            pw = click_module.prompt(
                "Upload password (press Enter to use default: 123456)",
                hide_input=True,
                default="123456",
                show_default=False,
            )
            pw = pw if pw else "123456"
            return pw
        return None

