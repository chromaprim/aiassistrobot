# Windows 新环境安装

## 1. 安装运行环境

推荐受 Docker Desktop 当前版本支持的 Windows 11 x64 电脑，启用 CPU 虚拟化，建议至少 8 GB 内存、20 GB 空闲磁盘。Windows 10 的版本、版本号及系统支持状态，Windows ARM 和企业管理策略请以 [Docker Desktop 官方要求](https://docs.docker.com/desktop/setup/install/windows-install/)为准。本项目 Windows 路线是 **Python 管理脚本 + Docker Desktop 中的 Linux 容器**。不支持 Docker Desktop 的 Windows Server 请改用 Linux 服务器版。

安装：

1. [Python 3](https://www.python.org/downloads/windows/)，建议 3.12，至少 3.9；安装时启用 Python launcher / PATH。本包不用 pip 安装管理依赖。
2. [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/)，按安装器提示启用 WSL 2 或受支持的后端。需要重启时先完成重启。
3. 手动启动 Docker Desktop，等待 Engine running，使用 **Linux containers**。不要在刚安装完、引擎未启动时运行本包。

如果选择 WSL 2 后端并缺少 WSL，在管理员 PowerShell 按微软/Docker 安装说明执行：

```powershell
wsl --install
```

必要时重启。已有 WSL 可用 `wsl --version` 检查；需要更新时运行 `wsl --update`。本包不自动安装系统虚拟化组件，也不自动修改企业电脑策略。

重新打开 PowerShell，检查：

```powershell
py -3 --version
docker version
docker compose version
docker info --format '{{.OSType}}'
```

最后一项应为 `linux`。若没有 `py` 但 `python --version` 可用，脚本会尝试 `python`。若输入 Python 打开了应用商店，请先修复 Python 安装或系统应用执行别名。

## 2. 下载、校验、完整解压

从 [Releases](https://github.com/chromaprim/aiassistrobot/releases/latest) 下载 Windows ZIP 和 `SHA256SUMS.txt`。在 PowerShell 中检查 ZIP：

```powershell
Get-FileHash .\aiassistrobot-qq-1.0.0-windows.zip -Algorithm SHA256
Get-Content .\SHA256SUMS.txt
```

比较文件名对应的 SHA256。资源管理器右键 ZIP →“全部解压”，例如解压到 `C:\aiassistrobot`。打开内层的 `aiassistrobot-windows` 文件夹。

不要在压缩包预览窗口内运行脚本；不要放入 OneDrive 等同步目录，也不要放到需要管理员写权限的 Program Files。后续生成的 QQ 会话和数据库都在此目录，别随手删除或公开同步。

## 3. 首次配置

在解压后的文件夹双击 `setup.cmd`。它会启动临时 PowerShell 脚本执行环境，不永久更改系统执行策略。也可以在该目录的 PowerShell 中执行：

```powershell
.\setup.cmd
```

按提示输入主人 QQ、DeepSeek Key、模型、自动记忆、其他 QQ 和群号。

- 主人 QQ 是找机器人聊天的账号；机器人用另一个 QQ 在网页扫码。
- Key 隐藏输入，粘贴后看不到字符，按回车继续。不要把 Key 填进命令行参数或提交到仓库。
- 默认模型 `deepseek-flash`，如果账户不支持，填账户真实可用的模型名称。
- 其他 QQ 和群号可留空，多个用逗号分隔。群中须 @机器人。

脚本生成配置、拉镜像、启动容器并检查网页和 API。首次日志在 `logs\first-run-时间.log`，状态在 `logs\first-run.status`；容器末尾日志在 `logs\containers-first-时间.log`。窗口最后会暂停，方便阅读错误。API 列表通过不代表余额充足或聊天已经成功。

镜像已提前导入时：

```powershell
.\setup.cmd -NoPull
```

重复执行使用已有配置，不覆盖 Key 和记忆。失败时先看错误再重跑，不要删除 `data`。

## 4. 登录两个网页

在当前目录右键 `credentials.txt` →“打开方式”→记事本，或：

```powershell
notepad .\credentials.txt
```

它是首次配置成功后才生成的文件。AstrBot 的用户名为 `astrbot`，初始随机密码见此文件；NapCat 使用文件中单独的 WebUI Token。

- AstrBot：<http://127.0.0.1:6185>，首次登录后修改密码。
- NapCat：<http://127.0.0.1:6099/webui>，登录后扫码绑定机器人 QQ。

Windows 同机运行不用 SSH。页面在另一台电脑上不能直接使用这两个 `127.0.0.1` 地址。固定配置只监听本机，请保持此设置。

`credentials.txt` 不含 DeepSeek Key。修改 AstrBot 密码后初始密码不更新；不要把主人 QQ 当 WebUI 用户名。

## 5. 日常启动和停止

先启动 Docker Desktop 并等待引擎就绪，再双击 `start.cmd`；停止双击 `stop.cmd`。它们不重新初始化数据。

在当前目录的 PowerShell 可用：

```powershell
.\manage.cmd status
.\manage.cmd start
.\manage.cmd restart
.\manage.cmd logs
.\manage.cmd doctor
.\manage.cmd access
.\manage.cmd backup
.\manage.cmd stop
```

查看日志按 Ctrl+C 退出，只退出日志查看，不停止机器人。命令行操作更适合保留输出，直接双击 `manage.cmd` 的窗口可能很快关闭。

容器设为 `unless-stopped`。Docker Desktop 必须先运行；可在它的设置中启用“登录时启动”，这通常依赖 Windows 用户已登录。**不能承诺电脑还在登录界面时自动运行**。手动 stop 的容器需要再次 start。

关闭脚本窗口不停止后台容器；退出 Docker Desktop、关机、休眠或断网会影响聊天。请按 [日常操作手册](OPERATIONS.md)验收记忆和回复。Windows 原生完整容器实测范围见 [VALIDATION.md](../VALIDATION.md)。
