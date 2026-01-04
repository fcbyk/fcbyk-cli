"""主窗口实现。"""

from __future__ import annotations

import sys

from ..core.compatibility import (
    QAction,
    QLabel,
    QMainWindow,
    QMenu,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
    Qt,
)
from .resources import create_app_icon


class MainWindow(QMainWindow):
    """主窗口。

    关闭按钮行为：默认不退出，而是隐藏到系统托盘；
    仅从托盘菜单选择“退出”才会真正关闭进程（类似网易云音乐）。
    """

    def __init__(self):
        super().__init__()

        self._is_quitting = False

        self.setWindowTitle("fcbyk CLI - GUI")

        # 限制窗口尺寸范围（避免过大/过小），同时不使用“最大化”
        self.resize(640, 420)
        self.setMinimumSize(640, 420)
        self.setMaximumSize(960, 700)

        # 取消标题栏最大化按钮（也会阻止标题栏双击最大化）
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        # 标题栏图标建议使用 16/24/32 等小尺寸，否则某些系统主题会出现裁剪。
        self.setWindowIcon(create_app_icon(prefer_titlebar_size=24))

        # 系统托盘
        self._setup_tray_icon()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        label = QLabel("Hello World!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(label)

        info_label = QLabel("这是 fcbyk CLI 的图形化界面版本")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

    def _setup_tray_icon(self):
        """初始化系统托盘与菜单。"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._tray_icon = None
            return

        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setIcon(create_app_icon(prefer_titlebar_size=24))
        self._tray_icon.setToolTip("fcbyk CLI - GUI")

        menu = QMenu()

        action_show = QAction("显示主窗口", self)
        action_show.triggered.connect(self.show_and_raise)
        menu.addAction(action_show)

        menu.addSeparator()

        action_quit = QAction("退出", self)
        action_quit.triggered.connect(self.quit_from_tray)
        menu.addAction(action_quit)

        self._tray_icon.setContextMenu(menu)

        # 双击托盘图标：显示窗口（各平台习惯略有差异，这里用 Activated 兼容）
        self._tray_icon.activated.connect(self._on_tray_activated)

        self._tray_icon.show()

    def _on_tray_activated(self, reason):
        # QSystemTrayIcon.ActivationReason
        try:
            trigger = QSystemTrayIcon.ActivationReason.Trigger
            double_click = QSystemTrayIcon.ActivationReason.DoubleClick
        except Exception:  # pragma: no cover
            trigger = QSystemTrayIcon.Trigger
            double_click = QSystemTrayIcon.DoubleClick

        if reason in (trigger, double_click):
            self.show_and_raise()

    def quit_from_tray(self):
        """从托盘菜单触发的真正退出。"""
        self._is_quitting = True
        # 先隐藏托盘图标，避免退出后残留
        if getattr(self, "_tray_icon", None) is not None:
            try:
                self._tray_icon.hide()
            except Exception:
                pass
        # 直接退出 Qt 事件循环（更可靠，避免仅 close 窗口但进程仍存活）
        try:
            from ..core.compatibility import QApplication

            app = QApplication.instance()
            if app is not None:
                app.quit()
                return
        except Exception:
            pass

        self.close()

    def closeEvent(self, event):  # noqa: N802
        """拦截窗口关闭按钮：默认隐藏到托盘。"""
        if self._is_quitting or self._tray_icon is None:
            event.accept()
            return

        event.ignore()
        self.hide()

        # 第一次提示用户已最小化到托盘
        if not getattr(self, "_tray_notice_shown", False):
            self._tray_notice_shown = True
            try:
                info = QSystemTrayIcon.MessageIcon.Information
            except Exception:  # pragma: no cover
                info = QSystemTrayIcon.Information

            self._tray_icon.showMessage(
                "fcbyk CLI - GUI",
                "程序已缩小到系统托盘。\n在托盘图标右键选择“退出”可完全关闭。",
                info,
                3000,
            )

    def _force_foreground_windows(self):
        """Windows 专用：使用 Win32 API 尽力将窗口置前。"""
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            SW_RESTORE = 9
            FLASHW_ALL = 3
            FLASHW_TIMERNOFG = 12

            class FLASHWINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.UINT),
                    ("hwnd", wintypes.HWND),
                    ("dwFlags", wintypes.DWORD),
                    ("uCount", wintypes.UINT),
                    ("dwTimeout", wintypes.DWORD),
                ]

            hwnd = int(self.winId())
            fg_win = user32.GetForegroundWindow()
            fg_tid = user32.GetWindowThreadProcessId(fg_win, None)
            our_tid = kernel32.GetCurrentThreadId()

            user32.AttachThreadInput(fg_tid, our_tid, True)
            user32.AllowSetForegroundWindow(-1)  # ASFW_ANY

            user32.ShowWindow(hwnd, SW_RESTORE)
            user32.SetForegroundWindow(hwnd)
            user32.SetFocus(hwnd)

            user32.AttachThreadInput(fg_tid, our_tid, False)

            if user32.GetForegroundWindow() != hwnd:
                info = FLASHWINFO(
                    cbSize=ctypes.sizeof(FLASHWINFO),
                    hwnd=hwnd,
                    dwFlags=FLASHW_ALL | FLASHW_TIMERNOFG,
                    uCount=0,
                    dwTimeout=0,
                )
                user32.FlashWindowEx(ctypes.byref(info))

        except Exception:
            self.raise_()
            self.activateWindow()

    def show_and_raise(self):
        """显示并激活窗口。

        Windows 上由于前台焦点限制，尽力置前；失败时会闪烁任务栏图标。
        """
        if self.isMinimized():
            self.showNormal()

        self.show()

        if sys.platform == "win32":
            self._force_foreground_windows()
        else:
            self.raise_()
            self.activateWindow()

