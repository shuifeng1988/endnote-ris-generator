# Zotero附件导入完整解决方案

## 问题根源

### 系统差异导致的路径问题
- **Windows系统**：RIS文件包含 `file:///C:/Users/...` 路径 → 在Linux上无效
- **Linux系统**：Zotero对RIS文件中的本地文件路径（`file:///media/...`）支持有限
- **结论**：不应依赖RIS文件的L1字段来关联本地附件

---

## 🎯 推荐方案

### 方案1：使用Zotfile插件 + 批量关联（⭐⭐⭐⭐⭐ 最推荐）

**Zotfile** 是Zotero最流行的附件管理插件，可以自动关联PDF。

#### 安装Zotfile

1. **下载插件**
   ```bash
   # 下载Zotfile
   wget https://github.com/jlegewie/zotfile/releases/latest/download/zotfile.xpi
   ```
   或访问：https://github.com/jlegewie/zotfile/releases

2. **安装到Zotero**
   - 打开Zotero
   - Tools → Add-ons
   - 点击齿轮图标 → Install Add-on From File
   - 选择下载的 `zotfile.xpi`
   - 重启Zotero

#### 使用步骤

1. **导入纯元数据RIS文件**（无附件路径）
   ```bash
   # 先生成无附件的纯元数据RIS
   python3 create_metadata_only_ris.py
   ```
   导入 `outputs2/out_ris_metadata_only/` 中的RIS文件到Zotero

2. **配置Zotfile**
   - Tools → Zotfile Preferences
   - **Source Folder**: 设置为你的PDF目录 `/media/shuifeng/BEA6-BBCE/pdfs`
   - **Use subfolder**: 不勾选
   - 勾选 "Automatically rename attachment files"

3. **批量关联PDF**
   - 在Zotero中选中所有导入的条目（Ctrl+A）
   - 右键 → Manage Attachments → Attach New File
   - Zotfile会自动根据文件名、DOI、标题匹配PDF
   - 或者：右键 → Manage Attachments → Get from Zotfile Source Folder

#### 优点
- ✓ 自动匹配PDF（基于文件名、DOI、标题）
- ✓ 可以重命名和组织附件
- ✓ 支持批量操作
- ✓ 可以移动附件到Zotero storage或保持链接

---

### 方案2：直接拖放PDF，自动识别元数据（⭐⭐⭐⭐）

如果你的PDF包含DOI或可识别的元数据：

1. **直接拖放PDF到Zotero**
   - 打开文件管理器，进入 `/media/shuifeng/BEA6-BBCE/pdfs`
   - 选中一批PDF文件
   - 直接拖放到Zotero的某个集合中

2. **Zotero自动识别**
   - Zotero会自动从PDF中提取DOI
   - 如果找到DOI，自动下载完整元数据
   - 如果没有DOI，会尝试从PDF内容识别

3. **手动修正**
   - 对于无法自动识别的，右键 → Retrieve Metadata for PDF
   - 或手动编辑元数据

#### 优点
- ✓ 最简单，一步到位
- ✓ 自动下载高质量元数据
- ✓ 适合大部分现代论文（包含DOI）

#### 缺点
- ✗ 需要PDF包含DOI或可识别文本
- ✗ 扫描版PDF可能无法识别

---

### 方案3：先导入RIS元数据，后手动关联PDF（⭐⭐⭐）

如果Zotfile无法自动匹配：

1. **导入纯元数据RIS**
   ```bash
   python3 create_metadata_only_ris.py
   ```

2. **手动关联PDF**
   - 在Zotero中选中一个条目
   - 点击工具栏的 📎 按钮（Add Attachment）
   - 选择 "Attach Link to File" 或 "Attach Stored Copy of File"
   - 浏览到对应的PDF文件

3. **批量关联（使用Python脚本）**
   我可以写一个脚本，通过Zotero API批量关联PDF

---

### 方案4：使用Zotero Connector（浏览器插件）（⭐⭐⭐⭐）

如果你能找到这些论文的在线版本：

1. **安装Zotero Connector**
   - Chrome/Firefox扩展商店搜索 "Zotero Connector"
   - 安装插件

2. **从网页导入**
   - 访问论文的DOI页面（如 https://doi.org/10.xxx）
   - 或访问PubMed、arXiv等数据库
   - 点击浏览器工具栏的Zotero图标
   - 自动保存元数据和PDF（如果可用）

---

## 🔧 实用工具和脚本

### 1. 创建纯元数据RIS

```bash
python3 create_metadata_only_ris.py
```

**输出**：`outputs2/out_ris_metadata_only/` - 按类别组织的无附件RIS文件

### 2. 创建PDF映射文件

```bash
python3 create_metadata_only_ris.py --create-mapping
```

**输出**：`outputs2/pdf_metadata_mapping.json` - PDF文件名到元数据的映射

### 3. 批量导入脚本（待创建）

如果需要，我可以创建一个Python脚本，使用Zotero API批量导入和关联附件。

---

## 📋 推荐工作流程

### 对于你的情况（163个分类文献）：

**第一步：安装Zotfile插件**
```bash
# 下载
wget https://github.com/jlegewie/zotfile/releases/latest/download/zotfile.xpi
# 然后在Zotero中安装
```

**第二步：生成纯元数据RIS**
```bash
python3 create_metadata_only_ris.py
```

**第三步：在Zotero中导入**
- 为每个类别创建集合
- 导入对应的RIS文件

**第四步：批量关联PDF**
- 配置Zotfile的Source Folder为 `/media/shuifeng/BEA6-BBCE/pdfs`
- 选中所有条目
- 右键 → Manage Attachments → Get from Zotfile Source Folder
- Zotfile会自动匹配PDF

---

## 🆚 方案对比

| 方案 | 难度 | 自动化程度 | 成功率 | 推荐指数 |
|------|------|------------|--------|----------|
| Zotfile插件 | 低 | 高 | 90%+ | ⭐⭐⭐⭐⭐ |
| 直接拖放PDF | 极低 | 高 | 70% | ⭐⭐⭐⭐ |
| 手动关联 | 中 | 低 | 100% | ⭐⭐⭐ |
| Zotero Connector | 低 | 高 | 95% | ⭐⭐⭐⭐ |

---

## ❓ 常见问题

### Q1: Zotfile无法匹配PDF怎么办？
A: 可能是文件名差异太大。可以：
   1. 重命名PDF为更标准的格式（作者_年份_标题）
   2. 使用DOI匹配（在Zotfile设置中启用）
   3. 手动关联剩余文件

### Q2: 如何保持PDF在原位置（不复制到Zotero storage）？
A: 在Zotfile中选择 "Attach Link to File" 而不是 "Attach Stored Copy"

### Q3: 可以先测试几个文件吗？
A: 可以！选择一个小类别（如只有5个文件的Multi-Omics）先测试

---

## 🚀 快速开始

```bash
# 1. 生成无附件RIS
python3 create_metadata_only_ris.py

# 2. 在Zotero中：
#    - 安装Zotfile插件
#    - 导入 outputs2/out_ris_metadata_only/Multi-Omics/ 中的RIS
#    - 配置Zotfile Source Folder
#    - 右键 → Manage Attachments → Get from Zotfile Source Folder

# 3. 检查附件是否正确关联
```

---

需要我创建任何其他工具或脚本吗？比如通过Zotero API自动批量导入的脚本？
