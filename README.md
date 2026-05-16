# 国内实习岗位 Career-Ops Lite

这个项目会定期搜索适合 2027 届数据类实习生的岗位，生成 Markdown 报告，并通过邮箱发送给你。

## 功能

- 目标城市：杭州、厦门、深圳
- 目标方向：数据分析、数据运营、商业分析、数据产品、AI 数据、模型评估
- 自动去重：`data/history.csv`
- 自动归档：`reports/YYYY-MM-DD.md`
- 云端定时：GitHub Actions 每 3 天运行一次
- 邮件发送：通过 SMTP，凭证读取 GitHub Secrets

## 本地运行

```powershell
python -m pip install -r requirements.txt
python -m src.scan --dry-run
```

只生成报告、不发邮件：

```powershell
python -m src.scan --no-email
```

## GitHub Secrets

在私有 GitHub 仓库中设置以下 Secrets：

- `MAIL_USERNAME`：发件邮箱账号，例如 `2804719869@qq.com`
- `MAIL_PASSWORD`：邮箱 SMTP 授权码，不是 QQ 登录密码
- `MAIL_TO`：收件邮箱，例如 `2804719869@qq.com`

QQ 邮箱需要在“设置 - 账号 - POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务”中开启 SMTP，并生成授权码。

## 注意

国内招聘网站可能存在登录、验证码或反爬限制。本项目只抓公开可访问页面，不自动登录、不绕过验证码、不自动投递。
