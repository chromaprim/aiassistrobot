# 常见问题排查

先在部署目录运行 `status`、`doctor`，再看 `logs`。Linux 对应 `sudo python3 manage.py 命令`；Windows 对应 `.\manage.cmd 命令`。不要用删除数据或重新初始化来试错。

## 网站打不开

- Windows：Docker Desktop 是否运行？是否为 Linux 容器？容器 `status` 是否正常？本机打开 <http://127.0.0.1:6185> / <http://127.0.0.1:6099/webui>。
- Linux 服务器：浏览器的 `127.0.0.1` 是浏览器所在电脑，远程时检查端口转发，而不是开放公网端口。参见 Linux 安装手册。
- `/data/statistics` 是 AstrBot 统计页，不是启动命令；`/webui/logs` 是 NapCat 日志页。网页关闭不等于机器人停止。
- 首次启动依赖加载可能需要时间。脚本最多等待约两分钟；超时后查看日志，修复后 `start`，不要并行开多个安装窗口。

宿主机端口占用：

Linux：

```bash
sudo ss -ltnp 'sport = :6185 or sport = :6099'
```

Windows PowerShell：

```powershell
Get-NetTCPConnection -State Listen -LocalPort 6185,6099 -ErrorAction SilentlyContinue
```

不要误关现有的远程管理隧道或另一套机器人。先确认占用者。如果调整 Compose 左侧宿主机端口，也要同步 `manage.py` 中网页检查端口和文档访问地址；初学者建议保留默认值并释放冲突。

## 用户名、密码或 Token 错误

AstrBot 用户名 `astrbot`，不是主人 QQ。`credentials.txt` 是本机普通文本文件，Linux 用 `sudo cat credentials.txt`，Windows 用 `notepad .\credentials.txt`。它仅在首次成功生成配置后存在。NapCat 使用其中单独的 WebUI Token，不用 AstrBot 密码或 DeepSeek Key。

AstrBot 改过密码时文件里的初始密码已经失效。忘记修改后的密码，请先备份并参考与你的框架版本对应的恢复办法，或恢复自己保存的有效配置备份；[上游 WebUI 说明](https://docs.astrbot.app/use/webui.html)可供核对登录机制。不要公开上传整个配置文件来求助，原始初始密码文件不能证明当前密码仍有效。

## QQ 在线但没有回复

1. 先用主人 QQ 私聊；检查主人是否填成了机器人自己的 QQ。
2. 其他用户/群是否加入白名单？群内是否 @机器人？机器人是否确实在群里？白名单用 `access` 更新，旧的完整名单需要重新填入。
3. AstrBot 的 OneBot 适配器是否已连接？NapCat 反向 WebSocket 应为 `ws://astrbot:6199/ws`，Token 与 AstrBot 配置一致。安装脚本已自动对齐，通常不用手改。
4. 日志有模型错误时，检查 DeepSeek 的 Key、API 余额、真实模型名和网络。网页版会员不代表 API 余额。
5. QQ 需重新扫码或设备验证时，由本人在 NapCat/手机 QQ 完成。社区接入可能受 QQ 更新或账号验证影响，不能保证永久免登录。

## Docker 或网络报错

- `docker` 不存在：先安装 Docker；Windows 安装后重新开终端，确认 PATH。
- Windows named pipe / daemon unavailable：先启动 Docker Desktop，等待引擎就绪。`OSType=windows` 需切 Linux containers。
- Linux permission denied：保持与首次部署一致的 sudo 用法。已有 root 数据不要直接用普通用户覆盖。
- 拉镜像失败：检查 Docker daemon 的代理/DNS，而不只是终端代理。先按 [官方 daemon 代理说明](https://docs.docker.com/engine/daemon/proxy/)配置，重试同一安装命令。
- 可把 Compose 中镜像仓库前缀换成自己信任的代理，保留 `@sha256:...`，校验内容摘要。不要改成未知 latest 整合包。本仓库默认使用官方镜像地址。
- 远程 Docker context 不适合本包：绑定目录必须位于运行脚本的同一主机。先检查 `docker context show`；Windows 通常为 Docker Desktop 的 Linux context。不要在本地运行脚本、却指向另一台 Docker 主机。

## API 检查或模型生成失败

`doctor` 不会发聊天生成请求。认证失败检查 Key；模型不在列表内会返回失败；列表通过后仍须发送一条真实 QQ 消息。超时检查目标机器能否访问 API；余额、限流、实际模型错误需看日志和 API 账户后台。

修改方式见 [日常操作](OPERATIONS.md#修改-key-或模型)。已保存的 Key 不会因为重跑 `setup` 被更新；不要期待重新启动后它再询问一次。

## 记忆没有生效

先用 `/记住 昵称=小明` 和 `/记忆` 验证手动保存。检查是同一个 QQ、同一个私聊/群空间；不同空间不会共享。人格编辑的是 `data/dafeiyu/persona.txt`，不是顶层模板。自动整理需要累计 8 条成功模型回复，且 `auto_memory` 开启；它不是逐字保存和准确召回全部历史。

提交问题时只提供版本、系统、经过遮盖的错误片段。安装日志可能包含 Token 或会话内容，请自己检查后再分享；不要提交配置、QQ 登录态和数据库。
