## run 命令

`run` 命令用于加载并执行可复用的脚本片段（命令集合）。
脚本以 JSON 文件形式维护，适合开发者手动编辑、版本管理和共享。

## 核心设计
* ❌ 不再提供 CLI 管理（add / rm / list）
* ✅ 仅保留 run 作为统一入口
* ✅ 脚本通过文件维护（更透明、可控）
* ✅ 支持占位符参数与工作目录
* ✅ 支持全局 + 本地覆盖
* ✅ 内置危险命令检测

## 数据存储

默认脚本文件：

```bash
~/.fcbyk/scripts.byk.json
```

本地覆盖文件（当前目录）：

```bash
./scripts.byk.json
```

### 加载规则

1. 先加载全局脚本
2. 若当前目录存在 `scripts.byk.json`：

   * 合并配置
   * **同名脚本以本地为准（覆盖全局）**

## 基本用法

```bash
fcbyk run <名称> [ARGS ...] [--cwd DIR]
```

- `<名称>`：要运行的脚本名称
- `ARGS ...`：传给脚本命令字符串的参数，对应 `$1` / `{1}` 等占位符
- `--cwd, -C DIR`：临时覆盖工作目录（优先级高于保存时的 cwd）

### 列出所有脚本(无参数)

```bash
fcbyk run
```

### 查看帮助

```bash
fcbyk run -h
```

---

## 脚本文件格式（scripts.byk.json）
```json
{
  "test": "pytset -q",
  "i": {
    "cmd": "npm i",
    "cwd": "/Users/coke/repo/fcbyk-cli/web-ui"
  }
}
```

## 执行流程

1. 加载全局 `scripts.byk.json`
2. 加载本地 `scripts.byk.json`（如存在）
3. 合并配置（本地优先）
4. 查找脚本
5. 替换参数占位符
6. 确定工作目录（优先级：CLI > 脚本定义）
7. 进行危险命令检测
8. 执行命令

## 注意事项

* `run` 会直接调用系统 shell 执行命令，请确保脚本内容安全可靠
* 建议将 `scripts.byk.json` 纳入版本控制（如 Git）
* 对于依赖路径的脚本，请合理设置 `cwd`
* JSON 格式错误会导致脚本加载失败，请确保语法正确


