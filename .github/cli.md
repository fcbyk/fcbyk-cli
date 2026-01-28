### pip 相关
```bash
pip install -e .
pip install -e .[test,gui]
pip uninstall -e fcbyk-cli
pip install fcbyk-cli
```

### 提交相关
```bash
cz commit
cz changelog --start-rev v0.2.2 --incremental
cz changelog --incremental
cz bump --files-only --changelog --allow-no-commit 0.2.3
cz bump 0.2.3
```

### 测试相关
```bash
pytest
pytest -q
```

### Git 相关
```bash
git tag -a v0.2.2 -m "release: v0.2.2"
git tag -d v0.2.2
git push --tags
git reflog
git reset --soft HEAD~1
git reset --soft 9ec989c
```

### Windows 清理 `__pycache__` 目录
```powershell
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
```

### 构建与发布
```bash
python -m build
twine upload dist/*
```
