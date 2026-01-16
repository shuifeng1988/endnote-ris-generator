# GitHub 上传指南 / GitHub Upload Guide

## 步骤 1: 在 GitHub 上创建新仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `endnote-ris-generator` (或你喜欢的名字)
   - **Description**: `A powerful AI-driven tool for generating EndNote and Zotero-compatible RIS files`
   - **Public/Private**: 选择 Public（公开）或 Private（私有）
   - **不要**勾选 "Initialize this repository with a README"（因为我们已经有了）
   - **不要**添加 .gitignore 或 license（我们已经有了）
3. 点击 "Create repository"

## 步骤 2: 添加远程仓库并推送

在你的本地项目目录中运行以下命令：

```bash
# 添加远程仓库（替换 YOUR-REPO-NAME 为你的仓库名）
git remote add origin https://github.com/shuifeng1988/YOUR-REPO-NAME.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

### 示例（假设仓库名为 endnote-ris-generator）：

```bash
git remote add origin https://github.com/shuifeng1988/endnote-ris-generator.git
git branch -M main
git push -u origin main
```

## 步骤 3: 验证上传

访问你的仓库页面：
```
https://github.com/shuifeng1988/YOUR-REPO-NAME
```

你应该能看到：
- ✅ README.md 显示在首页
- ✅ 所有源代码文件
- ✅ 文档目录
- ✅ 中英文 README 链接

## 可选：添加 LICENSE 文件

如果你想添加 MIT License：

```bash
# 创建 LICENSE 文件
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2026 shuifeng1988

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# 添加并提交
git add LICENSE
git commit -m "Add MIT License"
git push
```

## 后续更新

当你修改代码后，使用以下命令更新 GitHub：

```bash
# 查看修改
git status

# 添加修改的文件
git add .

# 提交修改
git commit -m "描述你的修改"

# 推送到 GitHub
git push
```

## 常见问题

### 1. 推送时要求输入用户名和密码

GitHub 已经不再支持密码认证，你需要使用 Personal Access Token (PAT)：

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. 选择权限：至少勾选 `repo`
4. 生成 token 并保存（只显示一次！）
5. 推送时使用 token 作为密码

### 2. 使用 SSH 代替 HTTPS

```bash
# 生成 SSH 密钥（如果还没有）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 添加 SSH 密钥到 GitHub
# 复制公钥内容：
cat ~/.ssh/id_ed25519.pub

# 访问 https://github.com/settings/keys 添加 SSH 密钥

# 修改远程仓库 URL
git remote set-url origin git@github.com:shuifeng1988/YOUR-REPO-NAME.git
```

## 推荐的仓库设置

在 GitHub 仓库页面：

1. **Settings → General**:
   - 添加 Topics: `python`, `endnote`, `zotero`, `ris`, `ai`, `llm`, `ocr`, `metadata-extraction`
   - 添加 Website: 你的项目主页（如果有）

2. **Settings → Features**:
   - ✅ Issues（启用问题跟踪）
   - ✅ Discussions（启用讨论功能）

3. **About**（仓库首页右侧）:
   - 添加描述
   - 添加 Topics
   - 添加 Website

## 完成！

你的项目现在已经在 GitHub 上了！分享链接：
```
https://github.com/shuifeng1988/YOUR-REPO-NAME
```

---

## Step 1: Create a New Repository on GitHub

1. Visit https://github.com/new
2. Fill in repository information:
   - **Repository name**: `endnote-ris-generator` (or your preferred name)
   - **Description**: `A powerful AI-driven tool for generating EndNote and Zotero-compatible RIS files`
   - **Public/Private**: Choose Public or Private
   - **DO NOT** check "Initialize this repository with a README" (we already have one)
   - **DO NOT** add .gitignore or license (we already have them)
3. Click "Create repository"

## Step 2: Add Remote Repository and Push

Run these commands in your local project directory:

```bash
# Add remote repository (replace YOUR-REPO-NAME with your repository name)
git remote add origin https://github.com/shuifeng1988/YOUR-REPO-NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Example (assuming repository name is endnote-ris-generator):

```bash
git remote add origin https://github.com/shuifeng1988/endnote-ris-generator.git
git branch -M main
git push -u origin main
```

## Step 3: Verify Upload

Visit your repository page:
```
https://github.com/shuifeng1988/YOUR-REPO-NAME
```

You should see:
- ✅ README.md displayed on homepage
- ✅ All source code files
- ✅ Documentation directory
- ✅ Chinese and English README links

## Optional: Add LICENSE File

If you want to add MIT License:

```bash
# Create LICENSE file
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2026 shuifeng1988

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF

# Add and commit
git add LICENSE
git commit -m "Add MIT License"
git push
```

## Future Updates

When you modify code, use these commands to update GitHub:

```bash
# Check modifications
git status

# Add modified files
git add .

# Commit changes
git commit -m "Describe your changes"

# Push to GitHub
git push
```

## Common Issues

### 1. Username and Password Required When Pushing

GitHub no longer supports password authentication. You need to use a Personal Access Token (PAT):

1. Visit https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select permissions: at least check `repo`
4. Generate token and save it (shown only once!)
5. Use token as password when pushing

### 2. Use SSH Instead of HTTPS

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add SSH key to GitHub
# Copy public key content:
cat ~/.ssh/id_ed25519.pub

# Visit https://github.com/settings/keys to add SSH key

# Change remote repository URL
git remote set-url origin git@github.com:shuifeng1988/YOUR-REPO-NAME.git
```

## Recommended Repository Settings

On GitHub repository page:

1. **Settings → General**:
   - Add Topics: `python`, `endnote`, `zotero`, `ris`, `ai`, `llm`, `ocr`, `metadata-extraction`
   - Add Website: your project homepage (if any)

2. **Settings → Features**:
   - ✅ Issues (enable issue tracking)
   - ✅ Discussions (enable discussions)

3. **About** (right side of repository homepage):
   - Add description
   - Add Topics
   - Add Website

## Done!

Your project is now on GitHub! Share the link:
```
https://github.com/shuifeng1988/YOUR-REPO-NAME
```
