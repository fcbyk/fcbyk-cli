# 命令别名

## 概述

`alias` 提供命令别名功能，支持通过配置文件定义命令映射。

```bash
byk <name> [...args]
```

## 配置加载

### 文件位置

- **全局配置**：`~/.fcbyk-cli/config/alias.byk.json`
- **本地配置**：`./alias.byk.json`（当前工作目录）

### 优先级

```
本地配置 > 全局配置（覆盖合并）
```

## 配置格式

- TypeScript 类型定义

```typescript
// 命令对象，`cmd` 必填，`cwd` 可选
export interface AliasCommand {
  cmd: string;
  cwd?: string;
}

// 联合类型，支持字符串或命令对象
export type AliasValue = string | AliasCommand;

// 递归接口，支持无限层级分组
export interface AliasConfig {
  [key: string]: AliasValue | AliasConfig;
}
```

- 配置示例

::: code-group

```json [简单模式]
{
  "dev": "vite",
  "build": "vite build",
  "test": "jest {args}"
}
```

```json [对象模式]
{
  "dev": {
    "cmd": "vite"
  },
  "install": {
    "cmd": "npm i",
    "cwd": "/Users/coke/project/web"
  },
  "lint": {
    "cmd": "eslint {0} --fix"
  }
}
```

```json [分组模式]
{
  "开发": {
    "测试": "pytest -q",
    "构建": {
      "前端": {
        "cmd": "pnpm run build",
        "cwd": "/Users/coke/repo/fcbyk-cli/web-ui"
      },
      "后端": "python -m build"
    }
  },
  "清理": "find . -type d ..."
}
```

:::

- 调用示例

```bash
byk dev             # vite
byk 开发.测试         # pytest -q
byk 开发.构建.前端     # pnpm run build (cwd: web-ui)
byk 清理             # find . -type d ...
```


## 执行流程

1. 检查内置插件命令 → 命中则执行
2. 加载并合并 alias 配置（本地 > 全局）
3. 查找匹配的 alias（支持分组路径）
4. 解析参数（占位符替换或自动透传）
5. 确定 cwd（CLI 参数 > 配置）
6. 安全检查（危险命令检测）
7. Shell 执行

## 参数处理

### 规则

| 条件 | 行为 |
|------|------|
| 无占位符 | 自动追加所有参数 |
| `{args}` | 替换为所有参数 |
| `{0}`, `{1}`, ... | 精确替换对应位置的参数（**支持非连续索引**） |

### 示例

**自动透传**
```json
"dev": "vite"
```
```bash
byk dev --port 3000
# 执行：vite --port 3000
```

**全量参数**
```json
"test": "jest {args}"
```
```bash
byk test src/index.test.js --coverage
# 执行：jest src/index.test.js --coverage
```

**精确参数（从 0 开始）**
```json
"lint": "eslint {0} --fix"
```
```bash
byk lint src/index.js
# 执行：eslint src/index.js --fix
```

**非连续索引（新功能）**
```json
"reorder": "echo {2} {0} {1}"
```
```bash
byk reorder A B C
# 执行：echo C A B
# 输出：C A B
```

**跳过第一个参数**
```json
"skip-first": "command --option {1}"
```
```bash
byk skip-first ignored value
# 执行：command --option value
```

**重复使用同一参数**
```json
"repeat": "echo {0} {0} {0}"
```
```bash
byk repeat Hello
# 执行：echo Hello Hello Hello
# 输出：Hello Hello Hello
```

## 工作目录（cwd）

### 配置方式

```json
{
  "install": {
    "cmd": "npm i",
    "cwd": "/project/web"
  }
}
```

### CLI 覆盖

```bash
byk install --cwd ./other-dir
```

**优先级**：`CLI 参数 > 配置文件`