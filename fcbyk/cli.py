#!/usr/bin/env python3
import click
from flask import Flask, send_from_directory, abort, render_template, request, jsonify
import os
from pathlib import Path
import re

app = Flask(__name__)
shared_directory = None

def safe_filename(filename):
    # 保留中文、字母、数字、空格、下划线、点、连字符
    return re.sub(r'[^\w\s\u4e00-\u9fff\-\.]', '', filename)

def get_path_parts(current_path):
    parts = []
    if current_path:
        path_parts = current_path.split('/')
        current = ''
        for part in path_parts:
            current = os.path.join(current, part)
            parts.append({
                'name': part,
                'path': current
            })
    return parts

@app.route('/')
def index():
    if not shared_directory:
        return "未指定共享目录，请使用 -d 参数指定目录"
    
    return serve_directory('')

@app.route('/<path:filename>')
def serve_file(filename):
    if not shared_directory:
        abort(404, description="未指定共享目录")
    
    file_path = os.path.join(shared_directory, filename)
    if not os.path.exists(file_path):
        abort(404, description="文件不存在")
    
    if os.path.isdir(file_path):
        return serve_directory(filename)
    
    return send_from_directory(shared_directory, filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    if not shared_directory:
        return jsonify({'error': '未指定共享目录'}), 400
    
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file:
        # 使用自定义的安全文件名函数
        filename = safe_filename(file.filename)
        # 确保文件名不为空
        if not filename:
            filename = '未命名文件'
        file.save(os.path.join(shared_directory, filename))
        return jsonify({'message': '文件上传成功'})
    
    return jsonify({'error': '上传失败'}), 500

def serve_directory(relative_path):
    current_path = os.path.join(shared_directory, relative_path)
    items = []
    
    for name in os.listdir(current_path):
        full_path = os.path.join(current_path, name)
        item_path = os.path.join(relative_path, name)
        items.append({
            'name': name,
            'path': item_path,
            'is_dir': os.path.isdir(full_path)
        })
    
    # 按目录优先排序
    items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
    
    # 获取共享目录的名称
    share_name = os.path.basename(shared_directory)
    
    return render_template('directory.html',
                         current_path=relative_path or '根目录',
                         path_parts=get_path_parts(relative_path),
                         items=items,
                         share_name=share_name)

@click.group()
def cli():
    pass

@cli.command()
@click.option("--name", default="fcbyk", help="Your name")
def hello(name):
    click.echo(f"⚡ Hello, {name}!")

@cli.command()
@click.option("-p", "--port", default=80, help="Port to run the web server on")
@click.option("-d", "--directory", required=True, help="Directory to share")
def web(port, directory):
    global shared_directory
    
    # 检查目录是否存在
    if not os.path.exists(directory):
        click.echo(f"❌ 错误：目录 {directory} 不存在")
        return
    
    if not os.path.isdir(directory):
        click.echo(f"❌ 错误：{directory} 不是一个目录")
        return
    
    # 转换为绝对路径
    shared_directory = os.path.abspath(directory)
    
    click.echo(f"🌐 启动文件共享服务器...")
    click.echo(f"📁 共享目录: {shared_directory}")
    click.echo(f"🔗 访问地址: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    cli()
