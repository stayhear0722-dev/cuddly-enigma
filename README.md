# 国内实习岗位 Career-Ops Lite

这个项目会定期搜索适合 2027 届数据类实习生的岗位，生成 Markdown 报告，并通过邮箱发送给你。

## 功能

- 目标城市：杭州、厦门、深圳
- 目标方向：默认数据分析、数据运营、商业分析、数据产品、AI 数据、模型评估
- 简历分析：优先读取 `RESUME_TEXT`，每次运行先分析简历文本，再动态调整岗位关键词、城市和匹配理由
- 本地上传：支持 PDF、DOCX、TXT 简历文件，本地提取文本后触发 GitHub Actions
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

## 上传简历并触发推荐

先复制 `.env.example` 为 `.env`，填入 GitHub Token：

```powershell
Copy-Item .env.example .env
```

`.env` 示例：

```text
GITHUB_TOKEN=你的 GitHub Token
GITHUB_REPOSITORY=stayhear0722-dev/cuddly-enigma
GITHUB_WORKFLOW=job-digest.yml
GITHUB_REF=main
```

安装依赖后，先 dry-run 检查简历能否解析：

```powershell
python -m pip install -r requirements.txt
python -m src.upload_resume --file "个人简历.pdf" --dry-run
```

确认画像正确后，正式触发云端推荐：

```powershell
python -m src.upload_resume --file "个人简历.pdf"
```

支持格式：

- `.pdf`
- `.docx`
- `.txt`

这个命令不会上传简历文件本身，只会把提取出的简历文本作为本次 GitHub Actions 输入传过去。

## GitHub Secrets

在私有 GitHub 仓库中设置以下 Secrets：

- `MAIL_USERNAME`：发件邮箱账号，例如 `2804719869@qq.com`
- `MAIL_PASSWORD`：邮箱 SMTP 授权码，不是 QQ 登录密码
- `MAIL_TO`：收件邮箱，例如 `2804719869@qq.com`
- `RESUME_TEXT`：可选，作为定时运行时的默认简历画像；手动运行时优先使用输入框里的 `resume_text`

QQ 邮箱需要在“设置 - 账号 - POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务”中开启 SMTP，并生成授权码。

## 手动为不同简历推荐岗位

进入 GitHub Actions 的 `Job Digest`，点击 `Run workflow`，在 `resume_text` 输入框粘贴本次简历正文。程序会优先分析这段文本，再推荐岗位。

更推荐使用本地上传命令 `python -m src.upload_resume --file "简历.pdf"`，这样不用手动复制正文。

建议粘贴：

- 年级、学历、专业
- 求职方向
- 目标城市
- 技能关键词
- 主要项目经历

不建议粘贴：

- 姓名
- 手机号
- 身份证号
- 家庭住址
- 邮箱密码或授权码

## 简历隐私

不要把 PDF/DOCX 简历或包含手机号、邮箱、身份证号的完整简历提交到仓库。本地上传命令会提示可能的敏感字段；如果你不希望这些字段进入 GitHub Actions 输入，请先删除或脱敏后再运行。

## 注意

国内招聘网站可能存在登录、验证码或反爬限制。本项目只抓公开可访问页面，不自动登录、不绕过验证码、不自动投递。
