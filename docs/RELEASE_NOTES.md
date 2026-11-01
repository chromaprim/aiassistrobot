# QQ 第一阶段 v1.0.0

- Linux：Python + Docker Engine / Compose，提供首次配置、首次日志和日常管理。
- Windows：Python + Docker Desktop（Linux 容器），提供 setup/start/stop 双击入口和命令行管理。
- QQ 私聊与群内 @ 回复；主人管理员与其他聊天白名单分开；按用户和群成员隔离的持久记忆。
- 固定 AstrBot / NapCat 镜像摘要，默认连接用户自己的 DeepSeek API；不含密钥、账号、聊天数据库或登录态。
- 随包附完整 Linux / Windows 安装、网页登录、配置、Token 节约、备份迁移和排错手册。

下载 `linux.tar.gz` 或 `windows.zip`，先阅读包内 README。两者都是联网部署包，依赖 Python 和 Docker；Windows 需要先启动 Docker Desktop 的 Linux 容器引擎。

SHA256 见附件 `SHA256SUMS.txt`。完整测试范围见仓库 `VALIDATION.md`；Windows 新环境的真实 QQ 登录和容器链路仍需按手册验收。本版未包含微信、抖音或直播。
