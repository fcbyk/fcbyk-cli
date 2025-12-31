import click
import os
import webbrowser
import pyperclip
import socket
from flask import Flask, send_from_directory, abort, render_template, request, jsonify, send_file
import re
from datetime import datetime
import urllib.request
import urllib.error

from fcbyk.cli_support.output import echo_network_urls
from fcbyk.utils.network import get_private_networks
# from fcbyk.utils.asset_downloader import create_web_assets_downloader
from ..web.app import create_spa


app = create_spa("lansend.html")
shared_directory = None
display_name = "共享文件夹"  # 默认显示名称
upload_password = None  # 上传密码
first_upload_log = True  # 控制首次日志前空一行

# 静态资源配置
# ASSETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'web', 'dist','assets')
# PRISM_VERSION = '1.29.0'
# STATIC_RESOURCES = {
#     'prism-tomorrow.min.css': f'https://cdn.jsdelivr.net/npm/prismjs@{PRISM_VERSION}/themes/prism-tomorrow.min.css',
#     'prism-core.min.js': f'https://cdn.jsdelivr.net/npm/prismjs@{PRISM_VERSION}/components/prism-core.min.js',
#     'prism-c.min.js': f'https://cdn.jsdelivr.net/npm/prismjs@{PRISM_VERSION}/components/prism-c.min.js',  # C++ 依赖 C
#     'prism-cpp.min.js': f'https://cdn.jsdelivr.net/npm/prismjs@{PRISM_VERSION}/components/prism-cpp.min.js',
#     'prism-python.min.js': f'https://cdn.jsdelivr.net/npm/prismjs@{PRISM_VERSION}/components/prism-python.min.js',
# }
# 创建资源下载器
# downloader = create_web_assets_downloader(STATIC_RESOURCES)

def init_app(directory=None, name=None, password=None, ide=False):
    global shared_directory, display_name, upload_password, ide_mode
    shared_directory = directory
    if name:
        display_name = name
    if password:
        upload_password = password
    ide_mode = ide


def _format_size(num_bytes):
    """字节数转可读字符串"""
    if num_bytes is None:
        return "unknown size"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024


def log_upload(ip, file_count, status, rel_path="", file_size=None):
    """统一的上传日志输出：时间 - IP - 文件数量 - 状态 - 相对路径 - 文件大小"""
    global first_upload_log
    # 第一次打印上传日志前先空一行，让它和 Flask 的启动信息之间有间隔
    if first_upload_log:
        print("", flush=True)
        first_upload_log = False

    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 使用 print，确保在 Flask 线程中也能正常输出，并立即刷新
    path_str = f"/{rel_path}" if rel_path else "/"
    size_str = _format_size(file_size) if file_size is not None else "unknown size"
    print(f"[{ts}] {ip} upload {file_count} file(s), status: {status}, path: {path_str}, size: {size_str}", flush=True)


def safe_filename(filename):
    return re.sub(r'[^\w\s\u4e00-\u9fff\-\.]', '', filename)

def get_path_parts(current_path):
    parts = []
    if current_path:
        path_parts = current_path.split('/')
        current = ''
        for part in path_parts:
            if part:  # 跳过空的部分
                current = os.path.join(current, part)
                parts.append({
                    'name': part,
                    'path': current
                })
    return parts

@app.route('/upload', methods=['POST'])
def upload_file():
    ip = request.remote_addr or 'unknown ip'
    # 前端会传递相对于共享根目录的路径（空字符串代表根目录）
    rel_path = (request.form.get('path') or '').strip('/')
    target_dir = os.path.abspath(os.path.join(shared_directory or '', rel_path))
    # 前端可提供 size（字节），用于日志显示
    size_hint = request.form.get('size')
    try:
        size_hint = int(size_hint) if size_hint is not None else None
    except (TypeError, ValueError):
        size_hint = None

    # 防止目录逃逸，确保目标目录在共享目录下
    if shared_directory and not target_dir.startswith(os.path.abspath(shared_directory)):
        log_upload(ip, 0, "failed (invalid path)", rel_path)
        return jsonify({'error': 'invalid path'}), 400

    # 仅做密码验证（没有文件）的请求：只验证密码并返回结果，不记录上传日志
    if 'file' not in request.files and 'password' in request.form:
        if upload_password:
            if request.form['password'] != upload_password:
                return jsonify({'error': 'wrong password'}), 401
            return jsonify({'message': 'password ok'})
        return jsonify({'error': 'upload password not set'}), 400

    if not shared_directory:
        log_upload(ip, 0, "failed (shared directory not set)", rel_path)
        return jsonify({'error': 'shared directory not set'}), 400
    
    if upload_password:
        if 'password' not in request.form:
            log_upload(ip, 0, "failed (upload password required)", rel_path)
            return jsonify({'error': 'upload password required'}), 401
        if request.form['password'] != upload_password:
            log_upload(ip, 0, "failed (wrong password)", rel_path)
            return jsonify({'error': 'wrong password'}), 401
    
    if 'file' not in request.files:
        log_upload(ip, 0, "failed (no file field)", rel_path)
        return jsonify({'error': 'missing file'}), 400
    
    file = request.files['file']
    # 尽量获取文件大小（字节）
    file_size = file.content_length if file.content_length not in (None, 0) else size_hint
    if file_size is None:
        try:
            pos = file.stream.tell()
            file.stream.seek(0, os.SEEK_END)
            file_size = file.stream.tell()
            file.stream.seek(pos, os.SEEK_SET)
        except Exception:
            file_size = None

    if file.filename == '':
        log_upload(ip, 0, "failed (no file selected)", rel_path)
        return jsonify({'error': 'no file selected'}), 400
    
    if file:
        filename = safe_filename(file.filename)
        if not filename:
            filename = 'untitled'
        
        # 检查文件是否已存在
        # 目标目录若不存在，直接报错，保持与目录结构一致
        if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
            log_upload(ip, 0, f"failed (target directory missing: {rel_path or 'root'})", rel_path)
            return jsonify({'error': 'target directory not found'}), 400

        target_path = os.path.join(target_dir, filename)
        if os.path.exists(target_path):
            # 生成新文件名
            name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(target_path):
                new_filename = "{}_{}{}".format(name, counter, ext)
                target_path = os.path.join(target_dir, new_filename)
                counter += 1
            filename = new_filename
        save_path = os.path.join(target_dir, filename)
        try:
            file.save(save_path)
            # 目前接口一次只支持上传一个文件，这里数量固定为 1
            log_upload(ip, 1, f"success ({filename})", rel_path, file_size)
            return jsonify({
                'message': 'file uploaded',
                'filename': filename,
                'renamed': counter > 1 if 'counter' in locals() else False
            })
        except Exception as e:
            log_upload(ip, 1, f"failed (save failed: {e})", rel_path, file_size)
            return jsonify({'error': 'failed to save file'}), 500
    
    return jsonify({'error': 'upload failed'}), 500

def get_file_tree(base_path='', relative_path=''):
    """递归获取目录树结构"""
    current_path = os.path.join(base_path, relative_path) if relative_path else base_path
    items = []
    
    if not os.path.exists(current_path) or not os.path.isdir(current_path):
        return items
    
    for name in os.listdir(current_path):
        full_path = os.path.join(current_path, name)
        item_path = os.path.join(relative_path, name) if relative_path else name
        
        item = {
            'name': name,
            'path': item_path.replace('\\', '/'),  # 统一使用 / 作为路径分隔符
            'is_dir': os.path.isdir(full_path)
        }
        
        if item['is_dir']:
            item['children'] = get_file_tree(base_path, item_path)
        
        items.append(item)
    
    items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
    return items

def is_image_file(filename):
    """检测文件是否为图片"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico', '.tiff', '.tif'}
    ext = os.path.splitext(filename)[1].lower()
    return ext in image_extensions

def get_file_content(relative_path):
    """获取文件内容（用于IDE模式）"""
    # 将URL路径中的 / 转换为系统路径分隔符
    normalized_path = relative_path.replace('/', os.sep)
    file_path = os.path.join(shared_directory, normalized_path)
    
    # 防止路径逃逸
    file_path = os.path.abspath(file_path)
    if not file_path.startswith(os.path.abspath(shared_directory)):
        abort(404, description="Invalid path")
    
    if not os.path.exists(file_path) or os.path.isdir(file_path):
        abort(404, description="File not found")
    
    # 如果是图片文件，返回图片信息（前端会直接请求图片URL）
    if is_image_file(file_path):
        return jsonify({
            'is_image': True,
            'path': relative_path,
            'name': os.path.basename(relative_path)
        })
    
    try:
        # 尝试以文本方式读取
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({
            'content': content,
            'path': relative_path,
            'name': os.path.basename(relative_path),
            'is_image': False
        })
    except UnicodeDecodeError:
        # 二进制文件，返回特殊标记，让前端显示"使用浏览器打开"按钮
        return jsonify({
            'is_binary': True,
            'path': relative_path,
            'name': os.path.basename(relative_path),
            'error': 'Binary file cannot be displayed'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<path:filename>')
def api_file(filename):
    """API: 获取文件内容（用于预览）"""
    if not shared_directory:
        return jsonify({'error': 'Shared directory not specified'}), 400
    return get_file_content(filename)

@app.route('/api/tree')
def api_tree():
    """API: 获取目录树"""
    if not shared_directory:
        return jsonify({'error': 'Shared directory not specified'}), 400
    tree = get_file_tree(shared_directory)
    return jsonify({'tree': tree})

@app.route('/api/directory')
def api_directory():
    """API: 获取目录信息（用于 lansend.html）"""
    if not shared_directory:
        return jsonify({'error': 'Shared directory not specified'}), 400
    
    # 从请求参数获取相对路径
    relative_path = request.args.get('path', '').strip('/')
    
    current_path = os.path.join(shared_directory, relative_path) if relative_path else shared_directory
    
    # 检查路径是否存在且为目录
    if not os.path.exists(current_path) or not os.path.isdir(current_path):
        return jsonify({'error': 'Directory not found'}), 404
    
    # 获取文件列表
    items = []
    for name in os.listdir(current_path):
        full_path = os.path.join(current_path, name)
        item_path = os.path.join(relative_path, name) if relative_path else name
        items.append({
            'name': name,
            'path': item_path.replace('\\', '/'),  # 统一使用 / 作为路径分隔符
            'is_dir': os.path.isdir(full_path)
        })
    
    items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
    
    # 获取路径部分
    path_parts = get_path_parts(relative_path)
    
    share_name = os.path.basename(shared_directory)
    
    return jsonify({
        'display_name': display_name,
        'share_name': share_name,
        'relative_path': relative_path,
        'path_parts': path_parts,
        'items': items,
        'require_password': bool(upload_password)
    })

@app.route('/api/download/<path:filename>')
def api_download(filename):
    """API: 下载文件"""
    if not shared_directory:
        abort(404, description="Shared directory not specified")
    
    # 将URL路径中的 / 转换为系统路径分隔符
    normalized_path = filename.replace('/', os.sep)
    file_path = os.path.join(shared_directory, normalized_path)
    
    # 防止路径逃逸
    file_path = os.path.abspath(file_path)
    if not file_path.startswith(os.path.abspath(shared_directory)):
        abort(404, description="Invalid path")
    
    if not os.path.exists(file_path) or os.path.isdir(file_path):
        abort(404, description="File not found")
    
    try:
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        abort(500, description=f"Error downloading file: {str(e)}")


def _lansend_impl(port, directory, name, password, no_browser, ide=False):

    global shared_directory, display_name, upload_password, ide_mode
    
    if not os.path.exists(directory):
        click.echo("Error: Directory {} does not exist".format(directory))
        return
    
    if not os.path.isdir(directory):
        click.echo("Error: {} is not a directory".format(directory))
        return
    
    shared_directory = os.path.abspath(directory)

    if name:
        display_name = name
    
    if password and not ide:
        upload_password = click.prompt('Upload password (press Enter to use default: 123456)', hide_input=True, default='123456', show_default=False)
        upload_password = upload_password if upload_password else '123456'
    else:
        upload_password = None
    
    private_networks = get_private_networks()
    local_ip = private_networks[0]['ips'][0]
    
    click.echo(f" * Directory: {shared_directory}")
    click.echo(f" * Display Name: {display_name}")
    if upload_password:
        click.echo(f" * Upload Password: Enabled")
    echo_network_urls(private_networks, port, include_virtual=True)
    
    try:
        pyperclip.copy("http://{}:{}".format(local_ip, port))
        click.echo(" * URL has been copied to clipboard")
    except:
        click.echo(" * Warning: Could not copy URL to clipboard")
    
    if not no_browser:
        webbrowser.open("http://{}:{}".format(local_ip, port))

    app.run(host='0.0.0.0', port=port)


@click.command(help='Start a local web server for sharing files over LAN')
@click.option(
    "-p", "--port",
    default=80,
    help="Web server port (default: 80)"
)
@click.option(
    "-d", "--directory",
    default='.',
    help="Directory to share (default: current directory)"
)
@click.option(
    "-n", "--name",
    help="Display name for the page title (default: '共享文件夹')"
)
@click.option(
    "-pw","--password",
    is_flag=True,
    default=False,
    help="Prompt to set upload password (default: no password, or 123456 if skipped)"
)
@click.option(
    "-nb","--no-browser",
    is_flag=True,
    help="Disable automatic browser opening"
)
def lansend(port, directory, name, password, no_browser, ide=False):
    _lansend_impl(port, directory, name, password, no_browser, ide)


@click.command(name='ls', help='alias for lansend')
@click.option(
    "-p", "--port",
    default=80,
    help="Web server port (default: 80)"
)
@click.option(
    "-d", "--directory",
    default='.',
    help="Directory to share (default: current directory)"
)
@click.option(
    "-n", "--name",
    help="Display name for the page title (default: '共享文件夹')"
)
@click.option(
    "-pw","--password",
    is_flag=True,
    default=False,
    help="Prompt to set upload password (default: no password, or 123456 if skipped)"
)
@click.option(
    "-nb","--no-browser",
    is_flag=True,
    help="Disable automatic browser opening"
)
def ls(port, directory, name, password, no_browser, ide=False):
    _lansend_impl(port, directory, name, password, no_browser, ide)