"""Pick 抽奖码管理子窗口。

说明：
- 从持久化 JSON 读取抽奖码
- 支持新增随机抽奖码
"""

from ..core.compatibility import QDialog, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTextEdit, QVBoxLayout

from fcbyk.utils import storage


class PickCodesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("抽奖码")
        self.resize(520, 420)

        self._codes_file = storage.get_path('pick_redeem_codes.json', subdir='data')

        layout = QVBoxLayout()
        self.setLayout(layout)

        row_add = QHBoxLayout()
        layout.addLayout(row_add)

        row_add.addWidget(QLabel("新增数量:"))
        self._inp_count = QLineEdit("10")
        self._inp_count.setFixedWidth(80)
        row_add.addWidget(self._inp_count)

        btn_add = QPushButton("新增")
        btn_add.clicked.connect(self._on_add)
        row_add.addWidget(btn_add)

        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self._refresh)
        row_add.addWidget(btn_refresh)

        row_add.addStretch(1)

        self._txt = QTextEdit()
        self._txt.setReadOnly(True)
        layout.addWidget(self._txt, 1)

        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self._refresh()

    def _load(self):
        data = storage.load_json(self._codes_file, default={'codes': {}}, create_if_missing=True, strict=False)
        if not isinstance(data, dict):
            data = {'codes': {}}
        if not isinstance(data.get('codes'), dict):
            data['codes'] = {}
        return data

    def _save(self, data):
        storage.save_json(self._codes_file, data)

    def _refresh(self):
        data = self._load()
        codes = data.get('codes', {})
        total = len(codes)
        used = 0
        for _, info in codes.items():
            if isinstance(info, dict) and info.get('used'):
                used += 1
        unused = total - used

        lines = []
        lines.append("文件: %s" % self._codes_file)
        lines.append("总数: %d  未用: %d  已用: %d" % (total, unused, used))
        lines.append("")

        for c, info in sorted(codes.items()):
            st = "USED" if (isinstance(info, dict) and info.get('used')) else "UNUSED"
            lines.append("%s  %s" % (c, st))

        self._txt.setPlainText("\n".join(lines))

    def _parse_count(self):
        raw = (self._inp_count.text() or '').strip()
        if not raw:
            return None
        try:
            v = int(raw)
        except Exception:
            return None
        return v

    def _on_add(self):
        n = self._parse_count()
        if n is None or n <= 0:
            QMessageBox.warning(self, "参数错误", "请输入大于 0 的整数")
            return
        if n > 100:
            QMessageBox.warning(self, "参数错误", "单次最多新增 100 个")
            return

        # 生成逻辑与 PickService 保持一致（长度 4）
        import random
        import string

        charset = string.ascii_uppercase + string.digits

        data = self._load()
        codes = data.get('codes', {})
        existed = set(codes.keys())

        new_codes = []
        tries = 0
        max_tries = max(100, n * 20)
        while len(new_codes) < n and tries < max_tries:
            tries += 1
            code = ''.join(random.choice(charset) for _ in range(4))
            if code in existed:
                continue
            existed.add(code)
            new_codes.append(code)
            codes[code] = {'used': False}

        data['codes'] = codes
        self._save(data)

        if new_codes:
            QMessageBox.information(self, "新增成功", "已新增 %d 个抽奖码" % len(new_codes))
        else:
            QMessageBox.warning(self, "新增失败", "未能生成新的抽奖码")

        self._refresh()

