# 可选 GitHub Actions 示例

本目录 YAML 是参考文件，GitHub 不会自动执行。首次发布采用人工执行本地测试、打包和上传 Release；GitHub 登录仅有普通仓库权限，没有要求使用者额外授权 workflow 权限。

仓库维护者需要自动化时，在拥有相应权限的环境将 `verify.yml` 和 `release.yml` 复制到 `.github/workflows/`，检查 Actions 设置后提交。验证示例在 Windows / Ubuntu 运行单元测试并打包；发布示例在 `qq-v*` 标签触发，两个系统测试通过后构建并上传 Release。版本号需和 `VERSION` 一致。

示例依赖 Actions 能够使用的标准托管 runner、actions/checkout、actions/setup-python 以及 gh CLI。它们只验证脚本，不会登录 QQ 或使用你的 DeepSeek Key。
