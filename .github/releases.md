# 发布流程

1. 前端构建
```bash
pnpm run build:flatten
```

2. 后端测试与构建
```bash
pytest
python -m build
```

3. 生成变更日志（需检查）
```bash
cz changelog --incremental
```

4. bump 版本
```bash
cz bump 0.2.3
```

5. 推送变更
```bash
git push --follow-tags
```

6. 发布 pip
```bash
twine upload dist/*
```
