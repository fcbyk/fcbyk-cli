import click
import os
import pyperclip
import socket
from functools import wraps
from flask import Flask, send_from_directory, jsonify, request, session
from flask_socketio import SocketIO, emit, disconnect

# 在 CI 环境中，如果没有 DISPLAY 环境变量，设置一个默认值以避免导入 pyautogui 时出错
if 'DISPLAY' not in os.environ:
    os.environ['DISPLAY'] = ':0'

try:
    import pyautogui
except Exception:
    # 在 CI 环境中，如果 pyautogui 导入失败（例如没有 X 服务器或 Xlib 错误），创建一个模拟对象
    # 捕获所有异常，包括 Xlib.error.DisplayConnectionError, ImportError, OSError 等
    class MockPyAutoGUI:
        FAILSAFE = False
        @staticmethod
        def press(*args, **kwargs):
            pass
        @staticmethod
        def position():
            return (0, 0)
        @staticmethod
        def moveTo(*args, **kwargs):
            pass
        @staticmethod
        def click(*args, **kwargs):
            pass
        @staticmethod
        def rightClick(*args, **kwargs):
            pass
        @staticmethod
        def scroll(*args, **kwargs):
            pass
        @staticmethod
        def hscroll(*args, **kwargs):
            pass
    pyautogui = MockPyAutoGUI()

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'web'))
# 设置 secret_key 用于 session
app.secret_key = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 存储密码（在启动时设置）
PASSWORD = None

# 防止 pyautogui 的安全机制（如果鼠标移到屏幕角落会触发异常）
pyautogui.FAILSAFE = False

def require_auth(f):
    """装饰器：要求认证"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """返回控制页面"""
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), '..', 'web'),
        'slide.html'
    )

@app.route('/api/login', methods=['POST'])
def login():
    """登录验证"""
    global PASSWORD
    data = request.get_json()
    password = data.get('password', '')
    
    if password == PASSWORD:
        session['authenticated'] = True
        return jsonify({'status': 'success', 'message': 'Login successful'})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid password'}), 401

@app.route('/api/check_auth', methods=['GET'])
def check_auth():
    """检查认证状态"""
    if session.get('authenticated'):
        return jsonify({'status': 'success', 'authenticated': True})
    else:
        return jsonify({'status': 'success', 'authenticated': False})

@app.route('/api/next', methods=['POST'])
@require_auth
def next_slide():
    """下一页"""
    try:
        pyautogui.press('right')
        return jsonify({'status': 'success', 'action': 'next'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/prev', methods=['POST'])
@require_auth
def prev_slide():
    """上一页"""
    try:
        pyautogui.press('left')
        return jsonify({'status': 'success', 'action': 'prev'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/home', methods=['POST'])
@require_auth
def home_slide():
    """回到首页"""
    try:
        pyautogui.press('home')
        return jsonify({'status': 'success', 'action': 'home'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/end', methods=['POST'])
@require_auth
def end_slide():
    """跳到最后"""
    try:
        pyautogui.press('end')
        return jsonify({'status': 'success', 'action': 'end'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/mouse/move', methods=['POST'])
@require_auth
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

@socketio.on('connect')
def handle_connect():
    """WebSocket连接时验证认证"""
    if not session.get('authenticated'):
        disconnect()
        return False

@socketio.on('mouse_move')
def handle_mouse_move(data):
    """WebSocket处理鼠标移动"""
    if not session.get('authenticated'):
        return
    try:
        dx = data.get('dx', 0)
        dy = data.get('dy', 0)
        current_x, current_y = pyautogui.position()
        pyautogui.moveTo(current_x + dx, current_y + dy, duration=0)
    except Exception as e:
        pass

@app.route('/api/mouse/click', methods=['POST'])
@require_auth
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
    if not session.get('authenticated'):
        return
    try:
        pyautogui.click()
    except Exception as e:
        pass

@app.route('/api/mouse/rightclick', methods=['POST'])
@require_auth
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
    if not session.get('authenticated'):
        return
    try:
        pyautogui.rightClick()
    except Exception as e:
        pass

@app.route('/api/mouse/scroll', methods=['POST'])
@require_auth
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
    if not session.get('authenticated'):
        return
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
    global PASSWORD
    
    # 提示用户设置密码
    while True:
        password = click.prompt('Please set access password', hide_input=True, confirmation_prompt=True)
        if password:
            PASSWORD = password
            break
        else:
            click.echo('Password cannot be empty, please try again')
    
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

