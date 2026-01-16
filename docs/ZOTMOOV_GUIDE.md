# 使用ZotMoov插件批量关联附件指南

## ZotMoov简介

**ZotMoov** 是专为Zotero 7设计的附件管理插件，是Zotfile的现代化替代品。

- GitHub: https://github.com/wileyyugioh/zotmoov
- 功能：自动关联PDF、重命名、移动、组织附件

---

## 🚀 完整导入流程（使用ZotMoov）

### 第一步：准备纯元数据RIS文件 ✓

我已经为你生成好了：
```
outputs2/out_ris_metadata_only/
├── Multi-Omics/              (5个RIS文件)
├── Drug-Screening/           (15个RIS文件)
├── Single-Cell-Analysis/     (18个RIS文件)
└── ... 共13个类别
```

### 第二步：配置ZotMoov

1. **打开ZotMoov设置**
   - 在Zotero中：Tools → ZotMoov Preferences
   - 或：Edit → Settings → ZotMoov

2. **配置源文件夹（Source Folder）**
   ```
   Source Folder: /media/shuifeng/BEA6-BBCE/pdfs
   ```

3. **配置附件关联规则**
   - **Attach Mode**: 选择 "Link to File"（链接模式）或 "Copy to Storage"（复制模式）
     - **Link to File**: 保持PDF在原位置，只创建链接（推荐，节省空间）
     - **Copy to Storage**: 复制PDF到Zotero storage（更安全，但占用空间）

4. **配置文件名匹配**
   - 勾选 "Match by filename"
   - 勾选 "Match by DOI"（如果支持）
   - 勾选 "Match by title"（如果支持）

### 第三步：导入RIS并关联附件

#### 方法1：先导入元数据，后批量关联（推荐⭐）

1. **导入纯元数据RIS**
   ```
   1. 在Zotero中创建集合（如"Multi-Omics"）
   2. File → Import 或直接拖放RIS文件
   3. 导入 outputs2/out_ris_metadata_only/Multi-Omics/ 中的所有文件
   ```

2. **批量关联PDF**
   ```
   1. 选中所有导入的条目（Ctrl+A）
   2. 右键 → ZotMoov → Attach from Source Folder
   3. ZotMoov会自动搜索并关联PDF
   ```

#### 方法2：直接拖放PDF（如果PDF包含元数据）

如果你的PDF包含DOI或可识别的元数据：
```
1. 直接将PDF从 /media/shuifeng/BEA6-BBCE/pdfs 拖入Zotero
2. Zotero会自动提取元数据
3. 不需要导入RIS文件
```

---

## 🔧 ZotMoov高级配置

### 配置重命名规则

如果你想让ZotMoov自动重命名PDF：

```
Rename Pattern: {%a_}{%y_}{%t}
```
- `{%a}`: 作者姓氏
- `{%y}`: 年份
- `{%t}`: 标题

例如：`Smith_2023_Deep_Learning_in_Genomics.pdf`

### 配置目标文件夹结构

如果你想让ZotMoov按类别组织PDF：

```
Destination Folder: /path/to/organized/pdfs
Subfolder Pattern: {%c}  (按集合名称)
```

---

## 📋 具体操作步骤（测试流程）

### 测试1：小规模测试（Multi-Omics类别）

```bash
# 1. 确认PDF文件存在
ls /media/shuifeng/BEA6-BBCE/pdfs/*.pdf | head -10

# 2. 在Zotero中：
#    - 创建"Multi-Omics"集合
#    - 导入 outputs2/out_ris_metadata_only/Multi-Omics/ 中的5个RIS文件
#    - 检查导入成功（应该有5个条目）

# 3. 配置ZotMoov
#    - Source Folder: /media/shuifeng/BEA6-BBCE/pdfs
#    - Attach Mode: Link to File

# 4. 批量关联PDF
#    - 选中所有5个条目
#    - 右键 → ZotMoov → Attach from Source Folder
#    - 等待处理完成

# 5. 验证
#    - 检查每个条目是否有📎图标
#    - 双击附件看是否能打开
```

### 测试2：批量导入所有类别

如果小规模测试成功，批量处理所有类别：

```python
# 我可以创建一个脚本自动执行以下步骤：
# 1. 列出所有类别
# 2. 为每个类别生成导入命令
# 3. 生成验证报告
```

---

## 🎯 文件名匹配优化

由于你的PDF文件名可能与RIS中的标题不完全匹配，我们需要优化匹配策略。

### 方案A：创建PDF文件名映射表

```bash
# 生成PDF到元数据的映射
python3 create_metadata_only_ris.py --create-mapping
```

这会生成 `outputs2/pdf_metadata_mapping.json`，包含：
```json
{
  "12864_2024_Article_10910.pdf": {
    "title": "Molecular evolution of toothed whale genes...",
    "doi": "10.1186/s12864-024-10910-1"
  }
}
```

### 方案B：重命名PDF以匹配标题

我可以创建一个脚本，将PDF重命名为更标准的格式，提高匹配率。

---

## 🔍 诊断和故障排除

### 问题1：ZotMoov无法找到PDF

**可能原因**：
1. 文件名不匹配
2. 源文件夹配置错误
3. 文件权限问题

**解决方法**：
```bash
# 检查PDF文件存在且可读
ls -la /media/shuifeng/BEA6-BBCE/pdfs/ | grep "12864_2024"

# 检查文件权限
chmod 644 /media/shuifeng/BEA6-BBCE/pdfs/*.pdf
```

### 问题2：匹配率太低

**优化策略**：
1. 使用DOI匹配（最准确）
2. 创建符号链接，使用标准化的文件名
3. 手动关联无法自动匹配的文件

---

## 🛠️ 辅助工具

### 工具1：验证附件匹配率

```bash
# 我可以创建一个脚本，统计：
# - 导入的条目数
# - 成功关联附件的数量
# - 匹配率
# - 未匹配的条目列表
```

### 工具2：批量创建文件名软链接

```bash
# 为每个PDF创建一个基于标题的软链接
# 提高ZotMoov的匹配率
```

---

## 📊 预期结果

### 使用ZotMoov（基于文件名匹配）
- **自动匹配率**：60-80%（取决于文件名规范程度）
- **手动处理**：20-40%
- **总耗时**：10-20分钟（对于138个文件）

### 使用DOI匹配（如果PDF包含DOI）
- **自动匹配率**：90-95%
- **手动处理**：5-10%
- **总耗时**：5-10分钟

---

## ✅ 下一步建议

### 立即可做：

1. **快速测试**（5分钟）
   ```
   - 导入 Multi-Omics 类别的5个RIS文件
   - 使用ZotMoov尝试关联PDF
   - 检查匹配率
   ```

2. **如果匹配率低**
   - 我创建一个脚本来优化文件名
   - 或者使用DOI直接下载元数据

3. **如果匹配率高**
   - 批量处理所有13个类别
   - 手动关联剩余的未匹配文件

---

## 🔄 我可以提供的额外工具

需要我创建以下哪个工具？

1. **PDF文件名标准化脚本**
   - 将PDF重命名为 `作者_年份_标题前50字符.pdf`
   - 提高ZotMoov匹配率

2. **批量验证脚本**
   - 检查哪些文献成功关联了附件
   - 生成未匹配的文件列表

3. **符号链接生成脚本**
   - 为每个PDF创建基于标题的软链接
   - 不改变原文件，只创建链接

4. **通过Zotero API自动导入和关联**
   - 完全自动化的Python脚本
   - 直接调用Zotero API

---

请告诉我：
1. 你想先测试Multi-Omics类别看效果如何？
2. 还是需要我先创建文件名优化工具？
3. 或者你已经用ZotMoov测试过，遇到了什么问题？
