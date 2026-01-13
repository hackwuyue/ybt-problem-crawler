# GitHub 上传指南

## 步骤 1：在 GitHub 上创建新仓库

### 1.1 访问 GitHub

进入 https://github.com/new

### 1.2 填写仓库信息

**仓库名称**：`ybt-problem-crawler`

**仓库描述**：
```
A powerful Python web crawler for YBT (一本通) Online Judge System. 
Features concurrent crawling, resume support, image processing, 
and automatic SQL generation.
```

**可见性**：Public（公开）

### 1.3 其他设置

- ✅ 勾选 "Initialize this repository with a README"（可选，我们会覆盖）
- ✅ 添加 `.gitignore` → 选择 "Python"
- ✅ 添加 License → 选择 "MIT License"

### 1.4 创建仓库

点击 "Create repository" 按钮

---

## 步骤 2：本地 Git 初始化

打开 PowerShell，进入项目目录：

```powershell
cd "g:\oj题库\pachong"
```

### 2.1 初始化 Git 仓库

```powershell
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### 2.2 添加远程仓库

将 `your_username` 替换为你的 GitHub 用户名：

```powershell
git remote add origin https://github.com/your_username/ybt-problem-crawler.git
```

### 2.3 验证配置

```powershell
git remote -v
# 应该显示:
# origin  https://github.com/your_username/ybt-problem-crawler.git (fetch)
# origin  https://github.com/your_username/ybt-problem-crawler.git (push)
```

---

## 步骤 3：准备上传文件

### 3.1 创建 .gitignore

```powershell
# 如果之前没有创建，现在创建
echo "__pycache__/" > .gitignore
echo "*.pyc" >> .gitignore
echo ".pytest_cache/" >> .gitignore
echo "*.log" >> .gitignore
echo "problems_*.json" >> .gitignore
echo "problems_*.sql" >> .gitignore
echo "image/" >> .gitignore
echo "data/" >> .gitignore
echo ".venv/" >> .gitignore
echo "venv/" >> .gitignore
```

### 3.2 创建 .github/workflows CI/CD 配置（可选）

创建文件 `.github/workflows/python-lint.yml`：

```yaml
name: Python Lint

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    - run: pip install flake8 pylint
    - run: flake8 yibentong.py --max-line-length=120
    - run: pylint yibentong.py --disable=C0111
```

### 3.3 验证项目文件

```powershell
# 检查关键文件是否存在
Get-Item yibentong.py, README.md, QUICKSTART.md, IMPLEMENTATION.md, LICENSE
```

---

## 步骤 4：添加并提交文件

### 4.1 查看文件状态

```powershell
git status
```

### 4.2 添加所有文件

```powershell
git add .
```

### 4.3 查看暂存区

```powershell
git status
# 应该显示所有待提交的文件
```

### 4.4 提交代码

```powershell
git commit -m "Initial commit: YBT Problem Crawler v1.0

- Complete web crawler for YBT Online Judge
- Concurrent crawling with ThreadPoolExecutor
- Resume support for interrupted crawls
- Automatic SQL generation
- Image processing and download
- Full CLI interface with argparse
- Comprehensive logging and error handling"
```

---

## 步骤 5：推送到 GitHub

### 5.1 推送主分支

```powershell
git push -u origin main
```

**注意**：如果主分支名是 `master`，使用：

```powershell
git push -u origin master
```

### 5.2 验证上传

进入 GitHub 仓库页面，检查文件是否已上传：
```
https://github.com/your_username/ybt-problem-crawler
```

---

## 步骤 6：完善 GitHub 项目页面

### 6.1 添加仓库主题（Topics）

在仓库设置中添加标签：
- `web-crawler`
- `python`
- `online-judge`
- `oj`
- `scraper`
- `ybt`
- `concurrent`

### 6.2 编写 README.md

确保 README 包含：
- ✅ 项目描述
- ✅ 主要特性
- ✅ 安装步骤
- ✅ 使用示例
- ✅ 项目结构
- ✅ 贡献指南

### 6.3 设置 GitHub Pages（可选）

1. 进入仓库 Settings
2. 选择 Pages
3. 选择 `main` 分支作为源
4. 选择 `/docs` 文件夹
5. 保存

---

## 步骤 7：添加文档和示例

### 7.1 创建示例脚本

创建 `examples/basic_crawl.py`：

```python
#!/usr/bin/env python3
"""
基础爬取示例
"""

from yibentong import crawl_problem, create_sql_file
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def make_session():
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=0.6, 
                  status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

if __name__ == '__main__':
    # 爬取单个题目
    session = make_session()
    problem = crawl_problem(1000, session)
    
    print(f"题目标题: {problem['title']}")
    print(f"题目描述: {problem['description'][:100]}...")
```

### 7.2 创建文档文件夹

```powershell
mkdir docs
echo "# YBT Problem Crawler Documentation" > docs/index.md
```

---

## 步骤 8：发布版本（Release）

### 8.1 创建 Release

在 GitHub 上：
1. 进入 Releases
2. 点击 "Create a new release"
3. 标签：`v1.0`
4. 标题：`YBT Problem Crawler v1.0 - Initial Release`
5. 描述：

```markdown
## 📋 功能

✅ 完整的爬虫框架
✅ 并发爬取（ThreadPoolExecutor）
✅ 断点续爬支持
✅ 自动 SQL 生成
✅ 完整 CLI 接口

## 🚀 快速开始

```bash
python yibentong.py 1000 1010 --concurrent 4
```

## 📦 安装

```bash
pip install requests beautifulsoup4 urllib3
```

详见 [README.md](https://github.com/your_username/ybt-problem-crawler/blob/main/README.md)
```

---

## 完整上传脚本

将以下内容保存为 `upload_to_github.ps1`：

```powershell
# GitHub 上传脚本

# 配置
$GitUsername = Read-Host "请输入 GitHub 用户名"
$RepoName = "ybt-problem-crawler"

# 步骤 1: 初始化
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 步骤 2: 添加远程
git remote add origin "https://github.com/$GitUsername/$RepoName.git"

# 步骤 3: 添加文件
git add .

# 步骤 4: 提交
git commit -m "Initial commit: YBT Problem Crawler v1.0"

# 步骤 5: 推送
git push -u origin main

Write-Host "✅ 上传完成！" -ForegroundColor Green
Write-Host "仓库地址: https://github.com/$GitUsername/$RepoName" -ForegroundColor Cyan
```

运行脚本：

```powershell
.\upload_to_github.ps1
```

---

## 常见问题

### Q: 推送时提示 "fatal: unable to access..."

**A: 需要生成 GitHub Token：**

1. 进入 https://github.com/settings/tokens
2. 点击 "Generate new token"
3. 勾选 `repo` 权限
4. 生成 token
5. 使用 token 作为密码推送：

```powershell
git push
# 用户名: your_username
# 密码: 粘贴 token
```

### Q: 推送时提示分支名错误

**A: 检查本地分支名：**

```powershell
git branch
# 如果是 'master' 而不是 'main'，使用：
git push -u origin master
```

### Q: 如何更新已上传的内容

```powershell
# 修改本地文件后
git add .
git commit -m "描述改动"
git push
```

### Q: 如何创建新分支

```powershell
git checkout -b feature/new-feature
git add .
git commit -m "Add new feature"
git push -u origin feature/new-feature
```

---

## 上传检查清单

- [ ] 已创建 GitHub 仓库（`ybt-problem-crawler`）
- [ ] 已初始化本地 Git
- [ ] 已设置 user.name 和 user.email
- [ ] 已添加远程仓库地址
- [ ] 已创建 `.gitignore` 文件
- [ ] 已添加所有源文件和文档
- [ ] 已提交代码（commit）
- [ ] 已推送到 GitHub（push）
- [ ] 已在 GitHub 上验证文件
- [ ] 已添加仓库描述和主题
- [ ] 已创建 Release（v1.0）

---

## 推荐的 GitHub 项目结构

```
ybt-problem-crawler/
├── yibentong.py                # 核心爬虫脚本
├── README.md                   # 项目描述
├── QUICKSTART.md               # 快速开始
├── IMPLEMENTATION.md           # 实现细节
├── COMPLETION_REPORT.md        # 完成报告
├── LICENSE                     # MIT License
├── .gitignore                  # Git 忽略规则
├── .github/
│   └── workflows/
│       └── python-lint.yml     # CI/CD 配置
├── examples/
│   ├── basic_crawl.py          # 基础爬取示例
│   ├── concurrent_crawl.py     # 并发爬取示例
│   └── resume_crawl.py         # 断点续爬示例
├── docs/
│   ├── index.md                # 文档首页
│   ├── api.md                  # API 参考
│   └── faq.md                  # 常见问题
└── requirements.txt            # Python 依赖
```

---

**祝上传顺利！🚀**

如有问题，参考 GitHub 官方文档：https://docs.github.com/
