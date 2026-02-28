## 简介

[![PyPI](https://img.shields.io/pypi/v/fcbyk-cli.svg)](https://pypi.org/project/fcbyk-cli/)
[![Tests](https://github.com/fcbyk/fcbyk-cli/actions/workflows/test.yml/badge.svg)](https://github.com/fcbyk/fcbyk-cli/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/fcbyk/fcbyk-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/fcbyk/fcbyk-cli)
[![License](https://img.shields.io/github/license/fcbyk/fcbyk-cli.svg)](https://github.com/fcbyk/fcbyk-cli/blob/main/LICENSE)

**`fcbyk-cli`** 是一个轻量、实用的命令行工具集合，

它用于通过终端快速完成一些 **零散但真实存在的需求**：
- 没有现成软件可用
- 或者已有软件过于臃肿、广告过多、不够轻量
- 又或者只是想用一条命令把事情做完

**`fcbyk-cli`** 的目标不是 “做一个大全”，  
而是用 **小而直接的工具**，解决当下遇到的问题。

如果你有实际需求或好的想法，也欢迎提交 [**issue**](https://github.com/fcbyk/fcbyk-cli/issues) 一起讨论。

## 已有功能 (子命令)

- [`lansend`](https://github.com/fcbyk/fcbyk-cli/blob/main/docs/LANSend.md)：在指定端口开启 `http服务器`，用于局域网内共享文件
- [`ai`](https://github.com/fcbyk/fcbyk-cli/blob/main/docs/AI.md)：在控制台与 `ai` 聊天 （需自行配置`api-key`）
- [`pick`](https://github.com/fcbyk/fcbyk-cli/blob/main/docs/Pick.md)：随机抽取一个元素（可用于抽奖、随机选择等）
- [`slide`](https://github.com/fcbyk/fcbyk-cli/blob/main/docs/Slide.md)：同一局域网内，手机控制电脑PTT翻页
- [`alias`](https://github.com/fcbyk/fcbyk-cli/blob/main/docs/Alias.md)：为常用命令添加别名，方便快速执行
- [`scripts`](https://github.com/fcbyk/fcbyk-cli/blob/main/docs/Scripts.md)：以脚本形式管理和运行常用命令
- [`get`](https://github.com/fcbyk/fcbyk-cli/blob/main/docs/Get.md)：资源获取，支持下载和打开官网
- [`config`](https://github.com/fcbyk/fcbyk-cli/blob/main/docs/Config.md)：查看数据目录、日志目录和配置文件路径

## 快速开始

- 使用 pip 安装

```bash
pip install fcbyk-cli
```

- 安装 GUI 依赖（可选）

```bash
pip install fcbyk-cli[gui]
```

- 显示帮助信息

```bash
fcbyk
```

## 运行环境说明

目前 **`fcbyk-cli`** 仅在 **Windows** 环境下进行过完整测试。

在 **Linux** 和 **macOS** 上可能可以运行，但暂未经过系统性验证，
如遇到问题，欢迎反馈。
