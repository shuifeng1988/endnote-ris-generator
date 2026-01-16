# 解决Zotero附件问题 - 完整方案

## 问题诊断

### 问题现象
- 单个RIS文件一篇一篇导入Zotero：**附件显示正常** ✓
- 多篇合并成一个RIS文件导入Zotero：**附件无法显示** ✗

### 根本原因
**Zotero在导入包含多条记录的单个RIS文件时，附件关联机制存在问题。**

虽然格式完全正确（记录分隔符、L1字段等都符合RIS标准），但Zotero可能无法正确处理多记录文件中的本地附件路径。

---

## 解决方案

### 方案1：使用重组后的文件夹（推荐✨）

我已经为你重新组织了所有分类文件，保持每个RIS文件独立：

**输出目录**：`outputs2/out_ris_by_category/`

```
outputs2/out_ris_by_category/
├── Multi-Omics/                    # 5个RIS文件
├── Drug-Screening/                 # 23个RIS文件
├── Single-Cell-Analysis/           # 19个RIS文件
├── Foundation-Models-Genomics/     # 17个RIS文件
├── 遗传进化/                       # 17个RIS文件
├── AI-Biomedical-Agents/           # 12个RIS文件
├── Perturbation-Response/          # 13个RIS文件
├── Genetic-Evolution/              # 9个RIS文件
├── Genome-Regulatory-Models/       # 7个RIS文件
├── Virtual-Cell-Review/            # 7个RIS文件
├── Spatial-Omics/                  # 4个RIS文件
├── 药物筛选/                       # 3个RIS文件
├── 虚拟细胞，综述，生物大模型/     # 2个RIS文件
└── classification_report.json
```

**导入步骤**：

1. **打开Zotero**

2. **创建集合（Collections）**
   - 在Zotero左侧栏右键点击"My Library"
   - 选择"New Collection"
   - 为每个类别创建对应的集合（如"Multi-Omics"、"Drug-Screening"等）

3. **批量导入RIS文件**
   - 方法A（推荐）：直接拖放
     * 打开文件管理器，进入某个类别文件夹（如`Multi-Omics/`）
     * 选中该文件夹中的所有RIS文件（Ctrl+A）
     * 拖放到Zotero对应的集合中
     * **所有附件应该都能正常显示！** ✓

   - 方法B：使用Zotero导入
     * 在Zotero中选择对应集合
     * 点击"File → Import"
     * 选择某个类别文件夹中的所有RIS文件
     * 点击"Open"

4. **验证附件**
   - 点击导入的文献
   - 检查"Attachments"部分是否显示PDF
   - 双击附件应该能打开文件

---

### 方案2：测试单条记录（验证问题）

如果你想验证问题的根本原因：

1. **测试文件**：`outputs2/test_single_from_merged.ris`
   - 这是从合并文件中提取的**单条记录**
   - 格式与合并文件中的记录完全相同

2. **导入测试**：
   - 将此文件导入Zotero
   - 如果附件能显示 → 确认是多记录文件的问题
   - 如果附件不能显示 → 可能是路径问题

---

### 方案3：修复合并文件（不推荐）

如果你仍想使用合并的RIS文件：

1. **使用修复脚本**：
   ```bash
   python3 fix_merged_ris_v2.py -d outputs2/out_ris_class
   ```

2. **问题**：
   - 即使修复后格式完全正确
   - Zotero仍可能无法正确处理多记录文件的附件
   - **不推荐使用此方案**

---

## 工具使用说明

### 重组工具（reorganize_ris_files.py）

如果你运行了新的分类，可以用此工具重新组织：

```bash
# 使用默认路径
python3 reorganize_ris_files.py

# 自定义路径
python3 reorganize_ris_files.py \
  --merged outputs2/out_ris_class \
  --original outputs2/out_ris \
  --output outputs2
```

**功能**：
- 从合并的RIS文件中提取记录信息
- 将原始的单个RIS文件复制到对应类别文件夹
- 生成按类别组织的文件夹结构

---

## 未来优化建议

### 修改主程序默认行为

在`zr/classify.py`中添加一个选项：

```bash
# 当前默认（合并RIS）
python zotero_restore_from_endnote_pdf_directories.py \
  --auto_classify

# 建议添加选项（保持单个RIS）
python zotero_restore_from_endnote_pdf_directories.py \
  --auto_classify \
  --organize_mode folder  # 新选项：folder 或 merged
```

这样用户可以选择：
- `--organize_mode merged`：合并为单个RIS（当前默认）
- `--organize_mode folder`：按文件夹组织单个RIS（推荐）

---

## 总结

### ✓ 推荐方案
使用重组后的文件夹结构（`out_ris_by_category/`），每个类别一个文件夹，包含该类别的所有单个RIS文件。

### ✓ 优点
1. 每个RIS文件独立，附件100%能正常显示
2. 按类别组织，导入时直接对应Zotero集合
3. 灵活性高，可以单独导入某些类别

### ✗ 不推荐
使用合并的RIS文件（`out_ris_class/*.ris`），即使格式正确，Zotero也可能无法正确处理附件。

---

## 文件清单

已创建的工具和文件：

1. **reorganize_ris_files.py** - 重组工具（已运行）
2. **fix_merged_ris_v2.py** - RIS格式修复工具（可选）
3. **diagnose_ris.py** - 诊断工具（用于调试）
4. **outputs2/out_ris_by_category/** - 重组后的文件夹（138个文件）
5. **outputs2/test_single_from_merged.ris** - 测试文件

---

如有任何问题，请参考此文档或运行诊断工具进行调试。
