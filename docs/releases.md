# 发布流程

```bash
# 前端构建
pnpm run build:flatten

# 后端测试
pytest

# 生成变更日志（需检查）
cz changelog --incremental

# bump 版本
cz bump x.y.z

# 推送变更
git push --follow-tags

# 发布 pip
python -m build
twine upload dist/*
```
