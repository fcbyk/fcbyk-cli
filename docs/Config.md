## Config 子命令

Config 子命令用于快速查看 `fcbyk-cli` 使用到的关键目录和配置文件位置，方便排查问题或手动编辑配置。

### 基本功能
- 显示数据目录位置
- 显示日志目录位置
- 显示主配置文件路径
- 显示脚本配置文件路径

### 基本用法
```bash
fcbyk config
```

执行后会依次输出：
- 数据目录路径
- 日志目录路径
- 配置文件路径（通常为 `fcbyk_config.json`）
- 脚本文件路径（通常为 `fscripts.json`）

示例输出（示意）：
```text
数据目录: C:\Users\<用户名>\.fcbyk
日志目录: C:\Users\<用户名>\.fcbyk\log
配置文件: C:\Users\<用户名>\.fcbyk\fcbyk_config.json
脚本文件: C:\Users\<用户名>\.fcbyk\fscripts.json
```

### 注意事项
- 该命令只负责**展示路径**，不会修改任何配置或文件内容。
- 若需要手动重置配置或清空数据，可根据该命令输出的路径自行删除或编辑对应文件。

