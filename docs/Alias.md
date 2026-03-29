# Alias 命令别名

## 概述

`alias` 提供命令别名功能，支持通过配置文件定义命令映射。

```bash
byk <name> [...args]
```

## 核心设计

- **统一模型**：不再区分 alias / script，统一为 alias
- **配置驱动**：通过 JSON 文件管理，无需 CLI 命令维护
- **Shell 执行**：直接使用 shell 执行命令
- **参数处理**：支持自动透传和占位符机制
- **层级分组**：支持递归嵌套的别名分组
- **工作目录**：支持配置 cwd 和 CLI 覆盖
- **安全检测**：内置危险命令识别

---

## 配置加载

### 文件位置

- **全局配置**：`~/.byk/alias.byk.json`
- **本地配置**：`./alias.byk.json`

### 优先级

```
本地配置 > 全局配置（覆盖合并）
```

---

## 配置格式

### 简单模式

```json
{
  "dev": "vite",
  "build": "vite build",
  "test": "jest {args}"
}
```

---

### 对象模式

```json
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

---

### 分组模式（递归嵌套）

支持通过对象嵌套实现别名分组，使用 **英文点号** `.` 作为路径分隔符：

```json
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

调用示例：

```bash
byk 开发.测试          # pytest -q
byk 开发.构建.前端     # pnpm run build (cwd: web-ui)
byk 清理                # find . -type d ...
```

---

### TypeScript 类型定义

```typescript
export interface AliasCommand {
  cmd: string;
  cwd?: string;
}

export type AliasValue = string | AliasCommand;

export interface AliasConfig {
  [key: string]: AliasValue | AliasConfig;
}
```

**类型说明：**
- `AliasCommand`：命令对象，`cmd` 必填，`cwd` 可选
- `AliasValue`：联合类型，支持字符串或命令对象
- `AliasConfig`：递归接口，支持无限层级分组

---

## 执行流程

```
1. 检查内置子命令 → 命中则执行
2. 加载并合并 alias 配置（本地 > 全局）
3. 查找匹配的 alias（支持分组路径）
4. 解析参数（占位符替换或自动透传）
5. 确定 cwd（CLI 参数 > 配置）
6. 安全检查（危险命令检测）
7. Shell 执行
```

---

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

### 参数异常

| 情况 | 行为 |
|------|------|
| 参数不足 | 报错 |
| 参数过多 | 报错 |

---

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

---

## 安全机制

### 危险命令检测

自动识别并阻止以下类型的命令：
- `rm -rf /` 等系统级删除操作
- `dd` 等底层磁盘操作
- 其他覆盖系统路径的操作

**行为**：默认提示并阻止执行

---

## 错误处理

- **字段缺失**：提示具体缺失的 key
- **参数不匹配**：报错并显示期望的参数数量
- **命令未找到**：提示无匹配的 alias

---

## 与旧版本差异

### 移除的功能

| 旧能力 | 状态 |
|--------|------|
| `fcbyk run` | ❌ 移除 |
| `fcbyk alias add` | ❌ 移除 |
| 命令序列数组 | ❌ 移除 |
| CLI 管理 alias | ❌ 移除 |

### 新模型

| 能力 | 新方式 |
|------|--------|
| 执行 | `byk <name>` |
| 管理 | 修改 JSON 文件 |
| 脚本 | alias |
| 参数 | 占位符 |
| 分组 | 递归嵌套对象 |

---

## 最佳实践

- ✅ 将 `alias.byk.json` 纳入版本控制
- ✅ 避免使用系统常见命令名（如 `ls`, `cd`）
- ✅ 对需要参数的命令使用 `{args}` 明确行为
- ✅ 复杂命令显式定义 `cwd`
- ✅ 使用分组组织相关命令
