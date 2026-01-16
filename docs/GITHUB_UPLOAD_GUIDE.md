# GitHub 上传指南

## 准备工作

### 1. 安装 Git

**Windows**:
- 下载 Git：https://git-scm.com/download/win
- 安装后打开 Git Bash

**macOS**:
```bash
brew install git
```

**Linux**:
```bash
sudo apt install git  # Ubuntu/Debian
sudo yum install git  # CentOS/RHEL
```

### 2. 配置 Git（首次使用）

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"
```

### 3. 创建 GitHub 账号

访问 https://github.com 注册账号（如果还没有）

## 上传步骤

### 方法一：通过命令行上传（推荐）

#### 1. 初始化 Git 仓库

在项目目录打开终端（Git Bash / Terminal）：

```bash
cd C:\Users\shuif\Desktop\Claude_code\001.zotera_create_ris\zotero_restoren_from_endnote

# 初始化 Git 仓库
git init

# 添加所有文件（.gitignore 会自动排除私人数据）
git add .

# 查看将要提交的文件
git status

# 提交到本地仓库
git commit -m "Initial commit: Zotero Literature Recovery Tool"
```

#### 2. 在 GitHub 创建远程仓库

1. 登录 GitHub
2. 点击右上角 "+" → "New repository"
3. 填写信息：
   - **Repository name**: `zotero-literature-recovery`
   - **Description**: `Intelligent tool to recover Zotero libraries from EndNote PDF directories using LLM`
   - **Public** 或 **Private**（选择公开或私有）
   - **不要**勾选 "Initialize this repository with a README"（我们已经有了）
4. 点击 "Create repository"

#### 3. 连接并推送到 GitHub

复制 GitHub 显示的命令，或使用以下命令：

```bash
# 添加远程仓库（替换 YOUR_USERNAME 为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/zotero-literature-recovery.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

**如果遇到认证问题**：
- GitHub 现在使用 Personal Access Token (PAT) 而不是密码
- 生成 PAT：GitHub → Settings → Developer settings → Personal access tokens → Generate new token
- 权限选择：`repo` (完整仓库访问)
- 使用 PAT 作为密码

### 方法二：通过 GitHub Desktop（图形界面）

#### 1. 安装 GitHub Desktop

下载：https://desktop.github.com/

#### 2. 添加本地仓库

1. 打开 GitHub Desktop
2. File → Add Local Repository
3. 选择项目目录：`C:\Users\shuif\Desktop\Claude_code\001.zotera_create_ris\zotero_restoren_from_endnote`
4. 如果提示"不是 Git 仓库"，点击 "Create a repository"

#### 3. 提交更改

1. 在左侧查看更改的文件
2. 填写 Commit message：`Initial commit: Zotero Literature Recovery Tool`
3. 点击 "Commit to main"

#### 4. 发布到 GitHub

1. 点击 "Publish repository"
2. 填写仓库名称和描述
3. 选择 Public 或 Private
4. 点击 "Publish Repository"

## 验证上传

### 检查 .gitignore 是否生效

上传后，访问你的 GitHub 仓库，确认以下文件/目录**没有**被上传：

- ❌ `.env` 文件（包含 API 密钥）
- ❌ `outputs/` 目录（包含处理结果）
- ❌ `logs/` 目录（可能包含敏感信息）
- ❌ `PDF/` 或 `Data/` 目录（私人文献数据）
- ❌ `state.jsonl` 文件（处理历史）

应该上传的文件：

- ✅ `README_CN.md` 和 `README_EN.md`
- ✅ `zotero_restore_from_endnote_pdf_directories.py`
- ✅ `zr/` 目录（所有 Python 模块）
- ✅ `requirements.txt`
- ✅ `.gitignore`
- ✅ `.env.example`（示例配置文件）

## 后续更新

### 添加新功能后更新

```bash
# 查看更改
git status

# 添加更改的文件
git add .

# 提交更改
git commit -m "描述你的更改"

# 推送到 GitHub
git push
```

### 常用 Git 命令

```bash
# 查看状态
git status

# 查看提交历史
git log --oneline

# 撤销未提交的更改
git checkout -- <file>

# 查看远程仓库
git remote -v

# 拉取最新代码
git pull
```

## 安全提示

### ⚠️ 重要：保护敏感信息

1. **永远不要**提交 `.env` 文件到 GitHub
2. **永远不要**提交包含 API 密钥的文件
3. **永远不要**提交私人文献数据（PDF、输出结果等）

### 如果不小心上传了敏感信息

#### 方法一：删除最近的提交（如果还没有推送）

```bash
# 撤销最后一次提交，保留更改
git reset --soft HEAD~1

# 从暂存区移除敏感文件
git reset HEAD <sensitive-file>

# 重新提交
git commit -m "Fixed commit"
```

#### 方法二：从历史中完全删除（已推送到 GitHub）

```bash
# 使用 BFG Repo-Cleaner 或 git filter-branch
# 详见：https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
```

**更简单的方法**：
1. 删除 GitHub 上的仓库
2. 重新创建仓库
3. 确保 `.gitignore` 正确配置后重新上传

## 添加 README 徽章（可选）

在 `README_CN.md` 和 `README_EN.md` 顶部添加：

```markdown
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![GitHub stars](https://img.shields.io/github/stars/YOUR_USERNAME/zotero-literature-recovery)
```

## 完成！

现在你的项目已经成功上传到 GitHub，可以：

1. 分享给其他人使用
2. 接收 Issues 和 Pull Requests
3. 使用 GitHub Actions 进行自动化测试
4. 添加到你的简历或作品集

**仓库地址示例**：
`https://github.com/YOUR_USERNAME/zotero-literature-recovery`
