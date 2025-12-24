import click
import os
import pyperclip
import socket
from flask import Flask, send_from_directory, jsonify, request
from flask_socketio import SocketIO, emit
import pyautogui

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'web'))
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 防止 pyautogui 的安全机制（如果鼠标移到屏幕角落会触发异常）
pyautogui.FAILSAFE = False

@app.route('/')
def index():
    """返回控制页面"""
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), '..', 'web'),
        'slide.html'
    )

@app.route('/api/next', methods=['POST'])
def next_slide():
    """下一页"""
    try:
        pyautogui.press('right')
        return jsonify({'status': 'success', 'action': 'next'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/prev', methods=['POST'])
def prev_slide():
    """上一页"""
    try:
        pyautogui.press('left')
        return jsonify({'status': 'success', 'action': 'prev'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/home', methods=['POST'])
def home_slide():
    """回到首页"""
    try:
        pyautogui.press('home')
        return jsonify({'status': 'success', 'action': 'home'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/end', methods=['POST'])
def end_slide():
    """跳到最后"""
    try:
        pyautogui.press('end')
        return jsonify({'status': 'success', 'action': 'end'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/mouse/move', methods=['POST'])
def mouse_move():
    """移动鼠标（HTTP接口，保留兼容性）"""
    try:
        data = request.get_json()
        dx = data.get('dx', 0)
        dy = data.get('dy', 0)
        current_x, current_y = pyautogui.position()
        pyautogui.moveTo(current_x + dx, current_y + dy, duration=0)
        return jsonify({'status': 'success', 'action': 'move'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@socketio.on('mouse_move')
def handle_mouse_move(data):
    """WebSocket处理鼠标移动"""
    try:
        dx = data.get('dx', 0)
        dy = data.get('dy', 0)
        current_x, current_y = pyautogui.position()
        pyautogui.moveTo(current_x + dx, current_y + dy, duration=0)
    except Exception as e:
        pass

@app.route('/api/mouse/click', methods=['POST'])
def mouse_click():
    """鼠标左键点击（HTTP接口，保留兼容性）"""
    try:
        pyautogui.click()
        return jsonify({'status': 'success', 'action': 'click'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@socketio.on('mouse_click')
def handle_mouse_click():
    """WebSocket处理鼠标左键点击"""
    try:
        pyautogui.click()
    except Exception as e:
        pass

@app.route('/api/mouse/rightclick', methods=['POST'])
def mouse_rightclick():
    """鼠标右键点击（HTTP接口，保留兼容性）"""
    try:
        pyautogui.rightClick()
        return jsonify({'status': 'success', 'action': 'rightclick'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@socketio.on('mouse_rightclick')
def handle_mouse_rightclick():
    """WebSocket处理鼠标右键点击"""
    try:
        pyautogui.rightClick()
    except Exception as e:
        pass

@app.route('/api/mouse/scroll', methods=['POST'])
def mouse_scroll():
    """鼠标滚动（HTTP接口，保留兼容性）"""
    try:
        data = request.get_json()
        dx = data.get('dx', 0)
        dy = data.get('dy', 0)
        if dy != 0:
            # pyautogui.scroll 需要整数，且值不能太大，限制在合理范围内
            scroll_clicks = int(round(dy))
            scroll_clicks = max(-100, min(100, scroll_clicks))
            if scroll_clicks != 0:
                pyautogui.scroll(scroll_clicks)
        if dx != 0:
            # 水平滚动也需要整数
            hscroll_clicks = int(round(dx))
            hscroll_clicks = max(-100, min(100, hscroll_clicks))
            if hscroll_clicks != 0:
                pyautogui.hscroll(hscroll_clicks)
        return jsonify({'status': 'success', 'action': 'scroll'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@socketio.on('mouse_scroll')
def handle_mouse_scroll(data):
    """WebSocket处理鼠标滚动"""
    try:
        dx = data.get('dx', 0)
        dy = data.get('dy', 0)
        if dy != 0:
            # pyautogui.scroll 需要整数，且值不能太大，限制在合理范围内
            scroll_clicks = int(round(dy))
            # 限制滚动值在 -100 到 100 之间，避免过大
            scroll_clicks = max(-100, min(100, scroll_clicks))
            if scroll_clicks != 0:
                pyautogui.scroll(scroll_clicks)
        if dx != 0:
            # 水平滚动也需要整数
            hscroll_clicks = int(round(dx))
            hscroll_clicks = max(-100, min(100, hscroll_clicks))
            if hscroll_clicks != 0:
                pyautogui.hscroll(hscroll_clicks)
    except Exception as e:
        pass

def _slide_impl(port):
    """slide 命令的实际实现"""
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    click.echo(f"\n * PPT Remote Control Server")
    click.echo(f" * Local URL: http://localhost:{port}")
    click.echo(f" * Local URL: http://127.0.0.1:{port}")
    click.echo(f" * Network URL: http://{local_ip}:{port}")
    click.echo(f" * Open the URL above on your mobile device to control")
    
    try:
        pyperclip.copy("http://{}:{}".format(local_ip, port))
        click.echo(" * URL has been copied to clipboard")
    except:
        click.echo(" * Warning: Could not copy URL to clipboard")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)

@click.command(name='slide', help='Start PPT remote control server, control slides via mobile web page')
@click.option(
    "-p", "--port",
    default=80,
    help="Web server port (default: 80)"
)
def slide(port):
    _slide_impl(port)

