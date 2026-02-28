## AI 子命令

AI 子命令用于在终端中与大模型聊天，支持：
- 使用本地配置文件保存/管理模型参数
- 在控制台以纯文本或 Markdown（富渲染）方式输出
- 支持流式输出（打字机效果）或一次性完整输出

### 基本功能
- 在终端内直接与大模型进行多轮对话
- 支持配置模型、API 地址、API Key 等参数并持久化
- 支持切换普通文本模式和富 Markdown 渲染模式
- 支持流式输出 / 非流式输出两种方式
- 支持用命令查看当前配置

### 基本用法
```bash
fcbyk ai [选项]
```

在没有额外参数时，`fcbyk ai` 会：
- 从统一配置文件中读取 `ai` section 的配置  
- 若未配置 `api_key`，会提示错误并退出  
- 否则进入交互式聊天模式

### 配置存储说明
- 所有与 AI 相关的配置统一存储在 `~/.fcbyk/fcbyk_config.json` 的 `ai` section 中
- 每次使用带参数的 `fcbyk ai` 调用，会更新并保存该 section 的配置
- 不带参数运行时，会读取已有配置并进入聊天

### 参数说明
- `-c, --config`  
  显示当前配置并退出，不进入聊天。  
  会展示配置文件路径、section 名以及当前配置内容。

- `-m, --model TEXT`  
  设置使用的模型名称，示例：`deepseek-chat`。  
  会写入配置文件的 `model` 字段。

- `-k, --api-key TEXT`  
  设置访问大模型接口所需的 API Key。  
  会写入配置文件的 `api_key` 字段。

- `-u, --api-url TEXT`  
  设置完整的 API 地址（如 `https://api.deepseek.com/v1/chat/completions`）。  
  会写入配置文件的 `api_url` 字段。

- `-s, --stream TEXT`  
  设置是否启用流式输出。  
  - `0` 或 `false`：关闭流式输出  
  - `1` 或 `true`：开启流式输出  
  会写入配置文件的 `stream` 布尔字段。

- `-r, --rich TEXT`  
  设置是否启用富渲染（Markdown + rich）。  
  - `0` 或 `false`：普通纯文本模式  
  - `1` 或 `true`：终端内使用 rich 渲染 Markdown  
  会写入配置文件的 `rich` 布尔字段。

### 常见用法示例

1. 查看当前配置
```bash
fcbyk ai --config
```

2. 首次配置 API Key 和模型
```bash
fcbyk ai -k sk-xxxxxx -m deepseek-chat
```
执行后会将配置保存到 `fcbyk_config.json` 中，对后续聊天生效。

3. 设置为流式输出 + 富渲染模式
```bash
fcbyk ai -s 1 -r 1
```

4. 使用当前配置开始聊天
```bash
fcbyk ai
```
进入后：
- 输入问题后回车发送
- 输入 `exit` 退出会话
- 也可以直接 `Ctrl+C`/`Ctrl+D` 结束

### 注意事项
- 使用前需要确保已正确配置 `api_key`，否则无法发起请求。
- 建议不要直接将真实密钥写入公开的配置文件或提交到版本控制。
- 富渲染模式依赖 `rich`，如未安装或终端不支持，仍会回退到普通文本输出。

