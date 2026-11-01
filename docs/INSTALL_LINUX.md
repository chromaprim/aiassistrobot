# Linux 新环境安装

## 1. 环境和依赖

推荐 Ubuntu 24.04 LTS x86_64。建议至少 2 核、4 GB 内存、10 GB 空闲磁盘，能够访问容器镜像仓库、QQ 和 DeepSeek API。固定镜像提供 Linux amd64 / arm64；ARM64 未做本项目端到端实测。

命令在**准备运行机器人的那台 Linux** 的终端执行。如何登录服务器由你的终端或云服务商控制台负责；下文安装和管理不要求固定使用 SSH 客户端。

检查环境：

```bash
uname -m
python3 --version
docker --version
docker compose version
```

要求 Python 3.9+、Docker Engine、Compose v2。Ubuntu/Debian 缺 Python 时：

```bash
sudo apt-get update
sudo apt-get install -y python3 ca-certificates curl
```

没有 Docker：先解压本包，再在解压目录运行：

```bash
sudo bash install-docker.sh
sudo docker info
sudo docker compose version
```

`install-docker.sh` 使用 Docker 官方 apt 仓库，只支持 Ubuntu/Debian；已有 Docker 时会停止，避免替换已有安装。已经安装 Docker 但缺 Compose 的机器，应按原安装来源补齐插件：官方 Docker apt 源一般用 `sudo apt-get install docker-compose-plugin`；发行版提供的包名可能是 `docker-compose-v2`，先用 `apt-cache policy docker-compose-v2 docker-compose-plugin` 确认。其他发行版按 [Docker 官方安装文档](https://docs.docker.com/engine/install/)操作。

Docker 无权限时，下文统一使用 `sudo`。不要时而用 root、时而用普通用户修改同一部署数据。本项目不自动把用户加入高权限的 docker 用户组。

## 2. 下载、校验、解压

从 [Releases](https://github.com/chromaprim/aiassistrobot/releases/latest) 下载 Linux 包和 `SHA256SUMS.txt`，放在同一目录。也可使用：

```bash
mkdir -p ~/aiassistrobot-download
cd ~/aiassistrobot-download
curl -fL -O https://github.com/chromaprim/aiassistrobot/releases/download/qq-v1.0.0/aiassistrobot-qq-1.0.0-linux.tar.gz
curl -fL -O https://github.com/chromaprim/aiassistrobot/releases/download/qq-v1.0.0/SHA256SUMS.txt
sha256sum aiassistrobot-qq-1.0.0-linux.tar.gz
cat SHA256SUMS.txt
tar -xzf aiassistrobot-qq-1.0.0-linux.tar.gz
cd aiassistrobot-linux
```

比较 Linux 文件对应的 SHA256；Windows 那行不用于 Linux 包。选择新的空目录安装，避免覆盖旧部署。

## 3. 首次配置并启动

```bash
sudo bash first-run.sh
```

如果当前用户已经有 Docker 权限且目录可写，可以不加 `sudo`。脚本先检查 Python、Docker、Linux 容器模式和端口，再询问：

| 提示 | 填写说明 |
| --- | --- |
| 主人 QQ | 你自己平时聊天用的 QQ。机器人用另一个 QQ 扫码 |
| API Key | 在终端隐藏输入；粘贴后看不到字符属于正常情况，按回车 |
| 模型 | 默认 `deepseek-flash`，以账户 `/models` 返回名称为准 |
| 自动记忆 | 默认开；填 `n` 可关闭，后续也能修改 |
| 其他 QQ | 可留空，或逗号分隔多个数字 QQ 号 |
| 群号 | 可留空，或逗号分隔群号；机器人还必须加入该群，群内 @才回复 |

脚本生成随机 WebUI 密码和内部连接 Token，拉取两镜像，启动容器，等待网页并查询模型列表。过程保存到 `logs/first-run-时间.log`；容器末尾日志保存到 `logs/containers-first-时间.log`；`logs/first-run.status` 保存结束状态。

- `READY_AWAITING_QQ_LOGIN`：网页和 API 检查通过，继续扫码与聊天验收。
- `API_CHECK_FAILED`：容器可能已启动，但 API 验证失败，按排错手册修复。
- `FAILED`：配置或启动中止，查看本次日志；修复原因后重跑同一命令。

重跑会沿用已生成配置，不重填 Key，也不清空记忆。拉镜像失败后可重跑；**不需要删除 `data/`**。命令缺依赖、尚未进入 Python 管理器时，只显示终端提示，可能尚未生成首次日志。

如果两固定摘要镜像已提前导入，可运行 `sudo bash first-run.sh --no-pull`；这只跳过拉取，QQ 和 API 仍须联网。

## 4. 打开管理网页

同一台 Linux 有桌面浏览器时，直接打开 <http://127.0.0.1:6185> 和 <http://127.0.0.1:6099/webui>。

在部署目录查看初始凭据：

```bash
sudo cat credentials.txt
```

AstrBot 用户名是 `astrbot`；随机首次密码和 NapCat WebUI Token 在该文件中。第一次登录 AstrBot 按提示修改密码。不要在用户名中填写主人 QQ。

无桌面的远程服务器：网页监听服务器自己的 `127.0.0.1`，你的日常电脑直接打开同一地址不会自动到达服务器。可以使用现有远程管理工具的端口转发功能，转发本地 6185→服务器 127.0.0.1:6185、本地 6099→服务器 127.0.0.1:6099；或在自己的电脑建立下面的回环隧道：

```bash
ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:6185:127.0.0.1:6185 -L 127.0.0.1:6099:127.0.0.1:6099 用户名@服务器地址
```

这条命令仅用于远程看网页，机器人启动和聊天不依赖隧道。保持转发窗口运行，再在自己的浏览器打开上述网页。如果本地端口占用，只把左侧改成 `16185` / `16099`，浏览器相应访问本地新端口。

不需要为管理页开放公网端口，不要把 Compose 中的回环绑定改成 `0.0.0.0`。内部 OneBot 6199 在 Docker 网络中使用，未映射到宿主机。

## 5. 扫码、验收、日常启动

NapCat 页面使用 Token 登录，扫码登录**机器人 QQ**，完成 QQ 要求的本人确认。AstrBot 中检查 OneBot 平台已连接。然后按 [实际聊天验收](OPERATIONS.md#实际聊天验收)完成测试。

日常无需重新配置：

```bash
cd ~/aiassistrobot-download/aiassistrobot-linux
sudo python3 manage.py status
sudo python3 manage.py start
```

如果你把包解压在其他路径，`cd` 应换成真实路径。Docker 服务启用、容器未被手动 stop 时，`unless-stopped` 会在 Docker 恢复时自动拉起容器；QQ 是否免扫码取决于登录态和平台验证。确认：

```bash
systemctl is-enabled docker
sudo python3 manage.py doctor
```

服务器保持开机、联网即可；你的日常电脑只在管理时需要打开。更多命令见 [日常操作](OPERATIONS.md)。
