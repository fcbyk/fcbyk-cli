## Alias 子命令

Alias 子命令用于为常用命令添加别名，方便快速执行。  
别名信息会统一保存在配置文件中，所有 `fcbyk` 调用共享。

### 基本功能
- 为任意已有子命令或子命令组合创建别名
- 列出当前所有别名及其对应真实命令
- 删除不再需要的别名
- 支持为复杂命令序列添加别名

### 配置存储说明
- 别名配置存储在 `~/.fcbyk/fcbyk_config.json` 的 `aliases` section 中
- 每个别名会映射到一个命令序列（列表），在解析时会被展开执行

### 基本用法
```bash
fcbyk alias [子命令] ...
```

支持的子命令：
- `add`：添加别名
- `list`：列出别名
- `remove`：删除别名

### 子命令与参数说明

#### 1. 添加别名：`alias add`

```bash
fcbyk alias add <别名> <真实命令及参数...>
```

- `<别名>`：要创建的别名名称，例如 `ll`、`deploy` 等
- `<真实命令及参数...>`：需要绑定的实际命令及其参数序列  
  例如：`pick --web -p 8080`、`scripts run deploy` 等

行为说明：
- 会校验 `<别名>` 是否与现有子命令重名，如重名则报错
- 会校验目标命令是否存在且参数合法
- 若别名已存在，会给出提示并覆盖旧配置

示例：
```bash
# 为 "fcbyk pick --web -p 8080" 创建别名 lp
fcbyk alias add lp pick --web -p 8080

# 为 "fcbyk scripts run deploy" 创建别名 deploy
fcbyk alias add deploy scripts run deploy
```

之后即可直接使用：
```bash
fcbyk lp
fcbyk deploy
```

#### 2. 查看别名：`alias list`

```bash
fcbyk alias list
```

- 列出当前所有已配置的别名及其映射的命令序列
- 当没有任何别名时，也会友好提示

#### 3. 删除别名：`alias remove`

```bash
fcbyk alias remove <别名>
```

- 若别名存在，则从配置中删除
- 若别名不存在，会给出错误提示

### 注意事项
- 别名仅在 `fcbyk` 命令内部生效，不影响系统 shell 的别名或函数。
- 别名解析时会被展开为真实命令序列再执行，因此仍遵循原命令的权限和行为。
- 为避免混淆，不建议使用已有子命令名作为别名名称。

