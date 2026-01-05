pip install -e .       # 安装当前项目
pip install -e ".[test]"  # 安装测试依赖
pytest                  # 测试
python -m build         # 构建
twine upload dist/*     # 上传

# Windows 清理 __pycache__ 目录
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force 