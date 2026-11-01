# 验证范围

本版整理日期：2026-11-01（Asia/Shanghai）。以下把既有 QQ 部署证据和此次打包验证分开，避免把模拟测试当成新机器真实登录结果。

## 既有 QQ 版本的验证

- Windows Python 3.12 中，使用真实 AstrBot v4.29.3、官方 Dashboard、本项目插件，接入模拟 OneBot WebSocket 和模拟 OpenAI 兼容模型。
- 私聊模型回复、人格注入、`/记住`、`/记忆`、8 次回复后的自动整理、重启和 `/new` 后召回，以及私聊/群/成员隔离和群内 @ 门控通过。模拟报告见 `tests/integration-report.json`，调用 13 次模拟模型；不是实际 DeepSeek 费用记录。
- 原目标 Ubuntu 24.04 x86_64 机器使用 Docker Engine 29.1.3、Compose 2.40.3，运行固定摘要的 AstrBot、NapCat 容器；通过可信代理获取与官方相同摘要内容，两管理页可访问。
- 该既有部署的 AstrBot 运行日志中已观察到 QQ 消息通过 DeepSeek 获得回复。这支持既有 Linux QQ 链路已运行，不等于所有新系统和账号都已验收。

这些私人日志、Key、QQ 账号和数据库都未随仓库公开。

## 本版可复现检查

```bash
python -m unittest discover -s tests -v
python scripts/build_release.py
docker compose config --quiet
```

单元测试覆盖：配置和随机 Token 对齐、特殊字符 Key 原样保存、不覆盖已有配置、非法输入写入前拒绝、QQ 白名单与管理员分离、记忆隔离、队列重试、容量、UTF-8 BOM、停服一致性备份与原运行状态恢复、首次日志及失败状态、模型不匹配、构建排除私人数据与可重复性。构建脚本分别生成带 LF 的 Bash 文件和带 CRLF 的 Windows 脚本。

本次在本地 Windows Python 3.12 上通过 18 项测试，包含带空格路径下的 Windows 管理入口和退出码；在 Linux 上核对 Bash 语法、Python 编译及 Compose 2.40.3 的配置解析。没有在检查目录启动 QQ 容器或使用私人 Key。

`docs/ci-examples/` 提供可选 GitHub Actions 示例，默认未启用。本次 GitHub 登录没有写入 workflow 的权限，采用本地构建并直接上传 Release；后续仓库维护者可以在权限具备时启用示例。不能把示例文件的存在视为云端 CI 已通过。

## 目标环境仍需验收

- 全新 Windows 上实际安装 Docker Desktop、容器启动、QQ 扫码和真实模型回复；本开发机尚无可用 Docker Desktop 引擎，此处不能宣称完成 Windows 容器端到端测试。
- Linux/Windows 整机重启、长时间在线、账号验证、Windows↔Linux 真实 QQ 登录态迁移。
- ARM64、其他发行版、企业管控电脑及多套部署同机运行。
- 用户 API 余额、费用和当前可用模型；安装时的 `/models` 检查不能代替真实生成验收。

每台新环境都应按 [实际聊天验收](docs/OPERATIONS.md#实际聊天验收)检查。默认是联网部署包，没有离线镜像和 GPU 模型。
