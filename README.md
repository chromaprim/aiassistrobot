# 大肥鱼 QQ 助手 · 第一阶段

在自己的 Linux 服务器或 Windows 电脑上运行 **AstrBot + NapCat + DeepSeek API**，提供 QQ 私聊、群内 @ 回复、人格和持久记忆。不需要 GPU；DeepSeek 使用云端 API，不会下载模型权重。

本次只包含 QQ 接入。微信、抖音、直播未包含在安装包中。代码和安装包都不包含使用者的 QQ 号、API Key、登录态或聊天数据库。

## 下载和安装

到 [Releases 下载页](https://github.com/chromaprim/aiassistrobot/releases/latest)，选择对应系统的包及 `SHA256SUMS.txt`。

| 运行环境 | 下载文件 | 安装入口 | 完整手册 |
| --- | --- | --- | --- |
| Linux，推荐 Ubuntu 24.04 x86_64 | `aiassistrobot-qq-1.0.0-linux.tar.gz` | `bash first-run.sh` | [Linux 安装](docs/INSTALL_LINUX.md) |
| Windows 11 x64 + Docker Desktop（Linux 容器） | `aiassistrobot-qq-1.0.0-windows.zip` | 解压后双击 `setup.cmd` | [Windows 安装](docs/INSTALL_WINDOWS.md) |

这是**联网安装包**，不内置 Python、Docker、容器镜像、模型或 QQ 登录态。首次拉取镜像需要联网，日常聊天也需要连接 QQ 和 DeepSeek API。Windows 版通过 Docker Desktop 运行 Linux 容器，不是免依赖的原生 EXE。

也可以下载仓库源码 ZIP，或 `git clone https://github.com/chromaprim/aiassistrobot.git`，进入源码目录后按对应系统手册操作。建议使用 Release 的固定版本；不要把源码更新覆盖到正在运行的数据目录。

## 配置时准备什么

1. 一个供机器人登录的 QQ 账号，用 NapCat 扫码登录。
2. 你平时用来找机器人聊天的 QQ 号，填入“主人 QQ”；它是管理员，**不是 WebUI 用户名**。其他用户和群可加入聊天白名单，群内须 @机器人。
3. 已开通 API 的 DeepSeek Key 和余额。Key 在本机终端隐藏输入，不需要发给任何人。默认模型 `deepseek-flash`，可填写账户实际可用的模型名。

## 两个管理网站

| 网站 | 地址 | 登录凭据 | 作用 |
| --- | --- | --- | --- |
| AstrBot | <http://127.0.0.1:6185> | 用户名 `astrbot`，首次随机密码见 `credentials.txt` | 模型、插件、聊天日志、统计 |
| NapCat | <http://127.0.0.1:6099/webui> | `credentials.txt` 中的 NapCat WebUI Token | QQ 扫码、在线状态、连接日志 |

`127.0.0.1` 指浏览器所在电脑。Windows 同机直接打开；远程 Linux 请按 [Linux 手册的远程访问说明](docs/INSTALL_LINUX.md#4-打开管理网页)建立回环转发或在服务器桌面浏览器访问。服务不会发布到公网。

首次修改 AstrBot 密码后，`credentials.txt` 中的初始密码不会同步更新。NapCat 的 WebUI Token、内部 OneBot Token、DeepSeek Key 是三种不同的凭据。

## 日常使用与验收

- [配置和日常操作](docs/OPERATIONS.md)：启停、多人白名单、凭据、人格、记忆、API 配置、日志。
- [备份、迁移和恢复](docs/BACKUP_MIGRATION.md)：把 Key、QQ 登录态和记忆一起迁移到自己的新设备。
- [故障排查](docs/TROUBLESHOOTING.md)：登录不了、没有回复、端口占用、Docker 和模型错误。
- [验证记录和局限](VALIDATION.md)：明确哪些是实测、哪些仍需在目标电脑验证。
- [来源、镜像版本和许可证](SOURCES.md)。

安装成功必须完成 [实际聊天验收](docs/OPERATIONS.md#实际聊天验收)：扫码后能收到回复、保存笔记、重启后能召回。管理网页能打开并不代表 QQ 已接通。

本包提供私聊按 QQ 隔离、群聊按群号和成员隔离的记忆。`/记住 昵称=小明` 明确保存，`/记忆` 查看，`/忘记 编号` 删除长期笔记。自动整理可选，每累计 8 条模型回复调用一次同一 API，另计费用；它不能保证记住所有内容。

## 开发和打包

只使用 Python 标准库进行管理、单元测试和构建；AstrBot 及其依赖运行在固定摘要的容器内。

```bash
python -m unittest discover -s tests -v
python scripts/build_release.py
```

产物在 `dist/`，包含 Linux / Windows 包和 SHA256 校验文件。构建只收录明确允许的程序、文档和插件，不收录 `data/`、`napcat/`、`credentials.txt`、`.env`、日志、备份或测试实例。自己的运行目录和私人备份请一直保留在本地。
