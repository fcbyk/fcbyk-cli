import os
import re
from typing import List, Dict


def get_files_metadata(path: str) -> List[Dict]:
    if not path or not os.path.exists(path):
        return []

    if os.path.isfile(path):
        return [{
            'name': os.path.basename(path),
            'path': path,
            'size': os.path.getsize(path)
        }]

    files = []
    try:
        for name in sorted(os.listdir(path)):
            full_path = os.path.join(path, name)
            if os.path.isfile(full_path):
                files.append({
                    'name': name,
                    'path': full_path,
                    'size': os.path.getsize(full_path)
                })
    except (FileNotFoundError, PermissionError):
        return []
    return files


def format_size(num_bytes: int | None) -> str:
    if num_bytes is None:
        return "unknown size"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.2f} {units[-1]}"


def safe_filename(filename: str) -> str:
    return re.sub(r"[^\w\s\u4e00-\u9fff\-\.]", "", filename)


def is_image_file(filename: str) -> bool:
    image_extensions = {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".tif"
    }
    ext = os.path.splitext(filename)[1].lower()
    return ext in image_extensions


def is_video_file(filename: str) -> bool:
    video_extensions = {
        ".mp4", ".webm", ".ogg", ".mov", ".mkv", ".avi", ".m4v"
    }
    ext = os.path.splitext(filename)[1].lower()
    return ext in video_extensions
