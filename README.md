# 国内实习岗位 Career-Ops Lite

这个项目会定期搜索适合 2027 届数据类实习生的岗位，生成 Markdown 报告，并通过邮箱发送给你。

## 功能

- 目标城市：杭州、厦门、深圳
- 目标方向：默认数据分析、数据运营、商业分析、数据产品、AI 数据、模型评估
- 简历分析：优先读取 `RESUME_TEXT`，每次运行先分析简历文本，再动态调整岗位关键词、城市和匹配理由
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
- `RESUME_TEXT`：可选，把简历正文粘贴到这里；不配置时使用通用数据类实习画像

QQ 邮箱需要在“设置 - 账号 - POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务”中开启 SMTP，并生成授权码。

## 简历隐私

不要把 PDF 简历或包含手机号、邮箱、身份证号的完整简历提交到仓库。推荐把简历正文放进 GitHub Actions Secret `RESUME_TEXT`。Secret 不会显示在代码里，运行时只用于生成本次岗位匹配画像。

## 注意

国内招聘网站可能存在登录、验证码或反爬限制。本项目只抓公开可访问页面，不自动登录、不绕过验证码、不自动投递。
