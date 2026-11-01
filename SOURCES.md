# 来源、固定版本与许可证

核对日期：2026-11-01（Asia/Shanghai）。这是自编的部署脚本和轻量记忆插件，采用 AstrBot + NapCat + DeepSeek API 组合；不是视频作者或任一上游发布的官方整合包。

| 组件 | 来源与版本 | 本仓库使用方式 |
| --- | --- | --- |
| AstrBot | [官方仓库](https://github.com/AstrBotDevs/AstrBot)，`v4.29.3`；[Docker 文档](https://docs.astrbot.app/deploy/astrbot/docker.html) | 拉取固定摘要的 `soulter/astrbot` 镜像，不内嵌框架源码或二进制；上游 AGPL-3.0-or-later |
| NapCat | [NapCatQQ](https://github.com/NapNeko/NapCatQQ)、[NapCat-Docker](https://github.com/NapNeko/NapCat-Docker) | 拉取固定摘要的 `mlikiowa/napcat-docker`；遵守各上游仓库和镜像组件许可证，本仓库 MIT 不覆盖它们 |
| DeepSeek | [API 文档](https://api-docs.deepseek.com/)、[当前模型说明](https://api-docs.deepseek.com/quick_start/pricing/) | 默认 API base `https://api.deepseek.com/v1`，模型 `deepseek-flash`；由用户填写自己的 Key |
| Docker | [Linux 安装](https://docs.docker.com/engine/install/)、[Windows 安装和要求](https://docs.docker.com/desktop/setup/install/windows-install/) | Linux 用 Engine + Compose；Windows 用 Docker Desktop 的 Linux 容器后端，许可按 Docker 条款 |
| 本仓库程序 | `manage.py`、启动脚本、记忆插件、测试和文档 | [MIT](LICENSE)，不改变上游许可证 |

启发视频：[想给大肥鱼完整的一生？DeepSeek接入QQ零基础教程，让她记住你](https://www.bilibili.com/video/BV1ZSnU6REuC/)。先前只核对过标题和 AstrBot / NapCat 标签，未取得完整字幕；本项目不声称逐项复制视频全部插件。

镜像固定内容（2026-10-30 查询官方 Registry 并核对架构索引）：

```text
soulter/astrbot:v4.29.3
sha256:c93a6d19507ba45474c3dfb82aad9d36eb432a478112f13c7e6325b5ebffc5f2

mlikiowa/napcat-docker（核对当日的 latest 内容）
sha256:b101b8968cc31ae428ec0f8e117386e4ced7773b2d8226ed9f7ddfcec55f1b7e
```

两个摘要均有 `linux/amd64`、`linux/arm64`。发布包不包含这些镜像本体，安装时下载；只更改可信代理仓库前缀且保留摘要时，Docker 仍按内容摘要校验。升级版本前先备份并核对平台、适配器、配置格式和插件兼容性。
