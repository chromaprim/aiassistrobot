# 配置和日常操作

所有命令在部署目录执行。Linux 以下按 sudo 部署举例；若你一直使用有 Docker 权限的普通用户，可以去掉 sudo。Windows 先运行 Docker Desktop，再在当前目录打开 PowerShell。

## 实际聊天验收

1. NapCat 登录机器人 QQ，检查它显示在线。
2. AstrBot 日志应出现 OneBot / `aiocqhttp` 适配器已连接。内部地址 `ws://astrbot:6199/ws` 已自动配置；不要改成 Windows 的 localhost。
3. 用主人 QQ 私聊机器人“你好”，应收到模型回复。
4. 发送 `/记住 昵称=小明`，收到保存确认；发送 `/记忆`，应看到笔记及编号。
5. Linux 运行 `sudo python3 manage.py restart`，Windows 运行 `.\manage.cmd restart`。等待 QQ 重新连上后，发送 `/new` 新建对话，再问“我叫什么”，确认长期笔记仍被召回。
6. 如果配置了其他用户、群：分别验证各自笔记隔离；群内 @才回复，不 @时不触发。群成员会看见群内问题和回答，群聊不是私聊。

实际收发、重启、记忆都验证后，才算这台机器安装完成。`doctor` 查询的是模型列表，不发聊天生成请求，不能证明余额和聊天生成可用。

## 命令对照

| 操作 | Linux | Windows PowerShell |
| --- | --- | --- |
| 首次安装/失败后继续 | `sudo bash first-run.sh` | `.\setup.cmd` |
| 已导入镜像，跳过拉取 | `sudo bash first-run.sh --no-pull` | `.\setup.cmd -NoPull` |
| 看容器状态 | `sudo python3 manage.py status` | `.\manage.cmd status` |
| 启动 | `sudo python3 manage.py start` | `.\manage.cmd start` |
| 停止 | `sudo python3 manage.py stop` | `.\manage.cmd stop` |
| 重启 | `sudo python3 manage.py restart` | `.\manage.cmd restart` |
| 看最近日志并持续跟踪 | `sudo python3 manage.py logs` | `.\manage.cmd logs` |
| 检查网页和模型列表 | `sudo python3 manage.py doctor` | `.\manage.cmd doctor` |
| 调整聊天白名单 | `sudo python3 manage.py access` | `.\manage.cmd access` |
| 停服一致性备份 | `sudo python3 manage.py backup` | `.\manage.cmd backup` |
| 查看初始登录凭据 | `sudo cat credentials.txt` | `notepad .\credentials.txt` |

`logs` 按 Ctrl+C 退出查看，容器继续运行。`start` 使用 Compose `up -d`，已有配置不变。`stop` 不删除容器数据；手动 stop 后不会自动恢复，需再次 start。

## 两种账号与三种密钥

- **机器人 QQ**：在 NapCat 扫码的 QQ，负责发消息。
- **主人 QQ**：在终端填入、平时向机器人发消息的 QQ，同时是管理员。
- **AstrBot WebUI**：用户名 `astrbot`，使用随机首次密码；修改后记住新密码。
- **NapCat WebUI Token**：用于登录 NapCat 管理网页。
- **内部 OneBot Token**：两容器互认的凭据，已自动匹配，日常不需要填写。
- **DeepSeek Key**：模型调用凭据，保存在本机 `data/cmd_config.json`。不会保存到 `credentials.txt`。

不要把 `credentials.txt` 发到聊天或提交 GitHub。已有部署只改 WebUI 密码，不需要重新运行初始化。修改密码后，该文件的初始密码不会同步更新。

## 多人、群聊和权限

运行 `access`，重新填写希望保留的**全部**其他 QQ 和群号，逗号或空格分隔。它替换旧集合，不是只追加一项。留空会清空对应的其他成员或群；主人自动保留。例：其他 QQ 输入 `223456789,323456789`，群输入 `88888888,99999999`，这些仅为格式示例。

此操作会备份配置，短暂停止 AstrBot，更新白名单和运行插件，再恢复。它保留 Key、聊天记录和笔记；其他 QQ 只获得聊天权限，不获得主人管理员权限。机器人需自己已经在相关群里，填群号不会自动加群。允许的群中，任何成员 @机器人都可能获得回复，笔记按成员隔离。

主人填错且尚未聊天时，可以先停止服务，备份，再在 `data/cmd_config.json` 修改 `admins_id`，在 `data/dafeiyu/settings.json` 修改 `owner_qq`，保存后运行 `access` 重建白名单。换主人不会自动转移旧 QQ 的笔记；请勿删除数据库来“修复”号码。

## 人格、记忆和节约 Token

| 文件/命令 | 用途 |
| --- | --- |
| `data/dafeiyu/persona.txt` | 运行中的人格，修改后下一条请求读取；UTF-8 保存 |
| 顶层 `persona.txt` | 仅首次初始化模板；部署后改它不影响当前人格 |
| `data/dafeiyu/settings.json` | `auto_memory`、QQ 白名单等插件设置 |
| `data/dafeiyu/memory.sqlite3` | 长期笔记和待自动整理队列 |
| `data/` 中 AstrBot 数据 | 框架聊天记录、对话上下文及配置 |
| `/记住 名称=内容` | 明确保存/更正当前空间的长期笔记 |
| `/记忆` | 看当前空间笔记和编号 |
| `/忘记 编号` | 删除当前空间的一条长期笔记 |
| `/new` | 由 AstrBot 新建当前聊天对话；不清空长期笔记 |

私聊按 QQ 号分开；群聊按群号和成员分开；私聊和群聊彼此分开。每个空间最多 80 项笔记，最多召回 12 项，采用简单文本匹配。手动笔记不会被自动整理覆盖。

自动记忆默认累计 8 次成功的模型回复后整理一次，使用同一个 Key，可能遗漏/提取错误并产生额外费用。整理失败会保留待整理消息重试。删除长期笔记不会删除旧聊天记录，后续讨论也可能再次形成相关记忆。

节约 Token：缩短人格，减少长消息和无用历史；不用持续话题时 `/new`；只放行需要的 QQ/群；在 `settings.json` 把 `"auto_memory": true` 改为 `false`，改用 `/记住`。框架会按配置在上下文超过阈值时压缩，压缩也需要模型调用；不要把上下文看成无限记忆。`auto_memory` 修改下一条消息生效，白名单请使用 `access`。

## 修改 Key 或模型

优先在 AstrBot WebUI 的模型配置中修改现有 DeepSeek 提供商及现有模型；修改后确认当前配置使用所选模型，保存并测试。不要仅新增一个模型却没有选为当前模型。

也可以停止服务、先备份，再用本机编辑器修改 `data/cmd_config.json`：

- `provider_sources` 中 `id` 为 `deepseek` 的项：`key` 是数组，例如 `["你本地填写的Key"]`；`api_base` 默认为 `https://api.deepseek.com/v1`。
- `provider` 中对应项的 `model` 填 API 接受的模型名。
- 如果同时改提供商或模型的 `id`，需要同步 `provider_source_id` 和 `agent_runner.config.model.provider_id`；只换 Key 或 `model` 字段无需改 ID。

不要把密钥放进命令行参数。保存为 UTF-8 JSON，保留双引号/逗号/括号，启动后运行 `doctor`，再用 QQ 发一条短消息验证真实生成。

## 日志与自启动

首次过程：`logs/first-run-时间.log`；首次状态：`logs/first-run.status`；容器片段：`logs/containers-first-时间.log`。日志可能带有网页登录 Token、QQ 信息或消息，只留在自己的设备。程序不记录你在配置时输入的 Key，依赖组件日志不能视为适合公开上传的内容。

额外保存一份当前容器日志：

Linux：

```bash
sudo docker compose logs --no-color --timestamps --tail 200 > containers-latest.log
```

Windows PowerShell：

```powershell
docker compose logs --no-color --timestamps --tail 200 | Out-File -Encoding utf8 .\containers-latest.log
```

Linux 使用 `systemctl is-enabled docker` 检查 Docker 自启动；如未启用且你希望开机启动，运行 `sudo systemctl enable --now docker`。Windows 在 Docker Desktop 设置中启用登录时启动，并确保电脑不休眠。两版均设置容器 `unless-stopped`，手动停止后仍需手动启动。
