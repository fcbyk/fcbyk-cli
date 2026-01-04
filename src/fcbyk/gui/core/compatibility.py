"""Qt 兼容层：统一 PySide6 / PyQt5 的导入。

注意：本模块只负责提供 Qt 类引用与 HAS_GUI 标志，不包含业务逻辑。
"""

from __future__ import annotations

HAS_GUI = False

try:
    from PySide6.QtWidgets import (
        QApplication,
        QMainWindow,
        QLabel,
        QVBoxLayout,
        QWidget,
        QSystemTrayIcon,
        QMenu,
        QHBoxLayout,
        QLineEdit,
        QPushButton,
        QFileDialog,
        QCheckBox,
        QMessageBox,
        QTextEdit,
        QSizePolicy,
    )
    from PySide6.QtCore import Qt, QByteArray
    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QCursor, QAction
    from PySide6.QtSvg import QSvgRenderer

    HAS_GUI = True
except ImportError:  # pragma: no cover
    try:
        from PyQt5.QtWidgets import (
            QApplication,
            QMainWindow,
            QLabel,
            QVBoxLayout,
            QWidget,
            QSystemTrayIcon,
            QMenu,
            QHBoxLayout,
            QLineEdit,
            QPushButton,
            QFileDialog,
            QCheckBox,
            QMessageBox,
            QTextEdit,
            QSizePolicy,
        )
        from PyQt5.QtCore import Qt, QByteArray
        from PyQt5.QtNetwork import QLocalServer, QLocalSocket
        from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QCursor, QAction
        from PyQt5.QtSvg import QSvgRenderer

        HAS_GUI = True
    except ImportError:  # pragma: no cover
        HAS_GUI = False


__all__ = [
    "HAS_GUI",
    "QApplication",
    "QMainWindow",
    "QLabel",
    "QVBoxLayout",
    "QHBoxLayout",
    "QWidget",
    "QSystemTrayIcon",
    "QMenu",
    "QAction",
    "QLineEdit",
    "QPushButton",
    "QFileDialog",
    "QCheckBox",
    "QMessageBox",
    "QTextEdit",
    "QSizePolicy",
    "Qt",
    "QByteArray",
    "QLocalServer",
    "QLocalSocket",
    "QIcon",
    "QPixmap",
    "QPainter",
    "QColor",
    "QFont",
    "QSvgRenderer",
    "QCursor",
]


