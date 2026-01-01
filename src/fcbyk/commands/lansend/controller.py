"""
lansend controller 层
负责 Flask 路由注册、请求解析、调用 service 并返回响应
"""

import os
import re
import mimetypes
from typing import Optional

from flask import abort, jsonify, request, send_file, Response, stream_with_context

from fcbyk.web.app import create_spa
from .service import LansendService


def create_lansend_app(service: LansendService):
    app = create_spa("lansend.html")
    app.lansend_service = service
    register_routes(app, service)
    return app


def _try_int(v) -> Optional[int]:
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def register_routes(app, service: LansendService):
    @app.route("/api/config")
    def api_config():
        return jsonify({
            "ide_mode": bool(getattr(service.config, "ide_mode", False)),
        })

    @app.route("/upload", methods=["POST"])
    def upload_file():
        ip = request.remote_addr or "unknown ip"
        rel_path = (request.form.get("path") or "").strip("/")
        size_hint = _try_int(request.form.get("size"))

        # 仅做密码验证（没有文件）的请求：只验证密码并返回结果，不记录上传日志
        if "file" not in request.files and "password" in request.form:
            if service.config.upload_password:
                if request.form["password"] != service.config.upload_password:
                    return jsonify({"error": "wrong password"}), 401
                return jsonify({"message": "password ok"})
            return jsonify({"error": "upload password not set"}), 400

        # shared_directory 必须存在
        try:
            target_dir = service.abs_target_dir(rel_path)
        except ValueError:
            service.log_upload(ip, 0, "failed (shared directory not set)", rel_path)
            return jsonify({"error": "shared directory not set"}), 400
        except PermissionError:
            service.log_upload(ip, 0, "failed (invalid path)", rel_path)
            return jsonify({"error": "invalid path"}), 400

        # 密码校验
        if service.config.upload_password:
            if "password" not in request.form:
                service.log_upload(ip, 0, "failed (upload password required)", rel_path)
                return jsonify({"error": "upload password required"}), 401
            if request.form["password"] != service.config.upload_password:
                service.log_upload(ip, 0, "failed (wrong password)", rel_path)
                return jsonify({"error": "wrong password"}), 401

        if "file" not in request.files:
            service.log_upload(ip, 0, "failed (no file field)", rel_path)
            return jsonify({"error": "missing file"}), 400

        file = request.files["file"]

        file_size = file.content_length if file.content_length not in (None, 0) else size_hint
        if file_size is None:
            try:
                pos = file.stream.tell()
                file.stream.seek(0, os.SEEK_END)
                file_size = file.stream.tell()
                file.stream.seek(pos, os.SEEK_SET)
            except Exception:
                file_size = None

        if file.filename == "":
            service.log_upload(ip, 0, "failed (no file selected)", rel_path)
            return jsonify({"error": "no file selected"}), 400

        filename = service.safe_filename(file.filename) or "untitled"

        if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
            service.log_upload(ip, 0, f"failed (target directory missing: {rel_path or 'root'})", rel_path)
            return jsonify({"error": "target directory not found"}), 400

        target_path = os.path.join(target_dir, filename)
        renamed = False
        if os.path.exists(target_path):
            name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(target_path):
                new_filename = f"{name}_{counter}{ext}"
                target_path = os.path.join(target_dir, new_filename)
                counter += 1
            filename = new_filename
            renamed = True

        save_path = os.path.join(target_dir, filename)
        try:
            file.save(save_path)
            service.log_upload(ip, 1, f"success ({filename})", rel_path, file_size)
            return jsonify({"message": "file uploaded", "filename": filename, "renamed": renamed})
        except Exception as e:
            service.log_upload(ip, 1, f"failed (save failed: {e})", rel_path, file_size)
            return jsonify({"error": "failed to save file"}), 500

    @app.route("/api/file/<path:filename>")
    def api_file(filename):
        try:
            data = service.read_file_content(filename)
            return jsonify(data)
        except ValueError:
            return jsonify({"error": "Shared directory not specified"}), 400
        except PermissionError:
            abort(404, description="Invalid path")
        except FileNotFoundError:
            abort(404, description="File not found")
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/tree")
    def api_tree():
        try:
            base = service.ensure_shared_directory()
        except ValueError:
            return jsonify({"error": "Shared directory not specified"}), 400
        tree = service.get_file_tree(base)
        return jsonify({"tree": tree})

    @app.route("/api/directory")
    def api_directory():
        try:
            relative_path = request.args.get("path", "").strip("/")
            data = service.get_directory_listing(relative_path)
            return jsonify(data)
        except ValueError:
            return jsonify({"error": "Shared directory not specified"}), 400
        except FileNotFoundError:
            return jsonify({"error": "Directory not found"}), 404

    @app.route("/api/preview/<path:filename>")
    def api_preview(filename):
        try:
            file_path = service.resolve_file_path(filename)
        except (ValueError, PermissionError):
            abort(404)

        if not os.path.exists(file_path) or os.path.isdir(file_path):
            abort(404)

        file_size = os.path.getsize(file_path)
        range_header = request.headers.get("Range", None)

        start = 0
        end = file_size - 1

        status_code = 200
        mimetype = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
        headers = {
            "Content-Type": mimetype,
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
        }

        if range_header:
            range_match = re.search(r"bytes=(\d+)-(\d*)", range_header)
            if range_match:
                start = int(range_match.group(1))
                if range_match.group(2):
                    end = int(range_match.group(2))
                else:
                    end = file_size - 1

                if start >= file_size or end >= file_size:
                    return Response(
                        "Requested Range Not Satisfiable",
                        status=416,
                        headers={"Content-Range": f"bytes */{file_size}"},
                    )

                length = end - start + 1
                headers["Content-Length"] = str(length)
                headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
                status_code = 206

        def generate_chunks(f, start_pos, size):
            with f:
                f.seek(start_pos)
                bytes_to_read = size
                while bytes_to_read > 0:
                    chunk_size = 1024 * 1024  # 1MB chunks
                    data = f.read(min(chunk_size, bytes_to_read))
                    if not data:
                        break
                    bytes_to_read -= len(data)
                    yield data

        file_handle = open(file_path, "rb")
        response_body = generate_chunks(file_handle, start, end - start + 1)

        return Response(stream_with_context(response_body), status=status_code, headers=headers)

    @app.route("/api/download/<path:filename>")
    def api_download(filename):
        try:
            file_path = service.resolve_file_path(filename)
        except ValueError:
            abort(404, description="Shared directory not specified")
        except PermissionError:
            abort(404, description="Invalid path")

        if not os.path.exists(file_path) or os.path.isdir(file_path):
            abort(404, description="File not found")

        try:
            return send_file(file_path, as_attachment=True)
        except Exception as e:
            abort(500, description=f"Error downloading file: {str(e)}")

