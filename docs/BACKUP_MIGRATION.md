# 备份、换机与恢复

## 备份包含什么

Linux 在部署目录运行 `sudo python3 manage.py backup`；Windows 运行 `.\manage.cmd backup`。

程序先记录哪些容器正在运行，再停止容器，归档 SQLite 和 QQ 数据，最后恢复此前运行的容器。原本停止的容器不会被额外启动。成功文件为 `backups/dafeiyu-时间.tar.gz`；中途失败的 `.partial` 不能用来恢复。

备份包括程序、文档、两系统启动脚本、Compose 固定镜像摘要、`data/`、`napcat/`、`.env`、`credentials.txt`。因此含 **API Key、网页凭据、QQ 登录态、聊天记录和长期笔记**。它与公开 Release 的空白包不同，不能上传仓库、网盘公开链接或随意发给他人。日志不包含在私人迁移备份中；需要时另行妥善保存。

备份不含 Docker 软件、镜像和云端模型，新环境仍须安装运行环境、拉取同一镜像。如果旧环境用了可信镜像代理，备份保留该 Compose 地址；新环境网络不适用时先核对固定摘要后再改回官方仓库地址。

## 恢复到 Linux

1. 按 Linux 安装手册准备 Python、Docker、Compose。
2. 把自己生成的备份传到新机器。旧机器先停止机器人，避免同一 QQ 两处运行。
3. 选择全新的空目录恢复，**不要覆盖正在运行的部署**。

```bash
mkdir -m 700 ~/aiassistrobot-restore
cd ~/aiassistrobot-restore
tar --no-same-owner -xzf /你的备份路径/dafeiyu-时间.tar.gz
cd aiassistrobot
sudo bash first-run.sh
```

本版备份的顶层目录为 `aiassistrobot`。早先本地试验包可能叫 `dafeiyu-linux`；先用 `tar -tzf /备份路径/文件.tar.gz` 查看，不要照抄不存在的路径。

跨用户/跨系统恢复时，NapCat 的 UID/GID 需要和数据属主匹配。若按上例统一用 sudo 运行，可在新机确认路径后，把**这次恢复目录**的属主设为 root，并设置 `.env` 为 root 的 UID/GID：

```bash
sudo chown -R root:root ./data ./napcat
printf 'NAPCAT_UID=0\nNAPCAT_GID=0\n' | sudo tee .env > /dev/null
sudo chmod 700 data napcat
sudo chmod 600 .env credentials.txt data/cmd_config.json napcat/config/onebot11.json napcat/config/webui.json
sudo bash first-run.sh
```

上面仅用于自己确认过的恢复目录，先前第一次启动失败也无需重新解压。若以普通用户管理，请改为其真实 UID/GID 和属主，不能混用。恢复已存在配置时不会重新问 Key；重新检查网页、扫码状态和记忆。

## 恢复到 Windows

1. 按 Windows 手册安装 Python、启动 Docker Desktop 的 Linux 容器引擎。
2. 把私人备份放在本地，用 Windows 自带 `tar` 解压到新空目录。

```powershell
New-Item -ItemType Directory C:\aiassistrobot-restore
Set-Location C:\aiassistrobot-restore
tar -xzf C:\你的备份路径\dafeiyu-时间.tar.gz
Set-Location .\aiassistrobot
.\setup.cmd
```

新建目录的路径请按实际情况调整。用自己的 Windows 账号保存和访问目录，NTFS 权限不同于 Linux 的 chmod。新硬件可能导致 QQ 重新验证，保存登录态不保证免扫码。

## 恢复后的检查

- 确认旧机器服务已停；新机两个管理页可登录，已有 QQ 白名单和模型正确。
- 机器人上线后，用原用户私聊 `/记忆`，检查原笔记；再测试群聊隔离和模型回答。
- 保留旧备份，直到新环境验证完成。不要为测试迁移而删掉唯一一份旧数据。
- Windows↔Linux 迁移的数据库和程序格式兼容；完整跨系统 QQ 会话迁移尚未在两台真实机器上验收，需按上述步骤复核权限和平台登录。

## 更新版本

先备份，再在新的目录准备新版本。保留旧的 `data/`、`napcat/`、`.env`、`credentials.txt`；不要让新旧两套同时运行。镜像按摘要固定，本包没有自动追踪 latest 的升级命令。需要更新镜像时核对上游兼容性、保留旧 Compose 和完整备份，更新后重新做收发和记忆验收。

卸载时先 stop 即可停止聊天；删除程序目录会同时删除未备份的数据。Docker 的全局清理命令可能影响别的项目，本手册不要求执行它们。
