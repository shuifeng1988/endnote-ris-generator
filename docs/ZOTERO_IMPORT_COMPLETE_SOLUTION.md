# Zotero PDF导入完整解决方案

## 当前问题
- Zotero Web API无法上传大PDF文件（413错误）
- ZotMoov创建链接而不是复制文件到Zotero存储
- U盘PDF需要永久存储到Zotero目录

## 最佳解决方案：分步导入

### 第1步：手动清理Zotero旧数据

由于API删除有问题，请在Zotero GUI中操作：

1. 打开Zotero桌面客户端
2. 在左侧集合列表中，选择所有测试集合（按住Ctrl多选）：
   - Uncategorized
   - ai_agents_biomedical
   - drug_screening
   - gene_regulation_networks
   - genomic_adaptation
   - models
   - multi_omics
   - mutli_omics
   - single_cell_analysis
   - virtual_cells
   - 以及任何其他测试集合
3. 右键点击 → 删除集合（Delete Collection）
4. 在确认对话框中选择"删除集合和条目"（Delete collection and items）
5. 等待删除完成

### 第2步：准备RIS文件（包含本地PDF路径）

使用原始的RIS文件（outputs2/out_ris_class），这些文件包含N1字段的PDF路径信息。

### 第3步：使用Zotero本地导入 + 首选项配置

#### 3.1 配置Zotero首选项

1. 打开Zotero → Edit → Preferences（编辑 → 首选项）
2. 进入"Advanced"（高级）→ "Files and Folders"（文件和文件夹）
3. **关键设置**：确保"Base directory"（基础目录）未设置
   - 如果有设置，点击"Choose..."清除它
   - 这样确保文件会被**复制**到Zotero存储目录
4. 确认"Linked Attachment Base Directory"为空

#### 3.2 导入RIS文件

由于Zotero不支持批量导入多个RIS文件，我们使用Python脚本自动化：

```bash
cd /home/shuifeng/Claude_code/001.zotera_create_ris/zotero_restoren_from_endnote

# 运行导入（使用API创建元数据 + 集合）
python3 auto_import_zotero.py
```

这将创建所有集合和元数据，但不包含附件。

### 第4步：使用ZotMoov批量复制PDF

#### 4.1 配置ZotMoov为复制模式

1. 在Zotero中，打开 Tools → ZotMoov Preferences
2. **关键设置**：
   - **Source Folder**（源文件夹）：`/media/shuifeng/BEA6-BBCE/pdfs`
   - **Destination Folder**（目标文件夹）：设置为Zotero存储目录
     - 通常是：`/home/shuifeng/Zotero/storage`
     - 或snap版本：`/home/shuifeng/snap/zotero-snap/common/Zotero/storage`
   - **Attachment File Operation**（附件文件操作）：
     - 选择 "**Copy/Import**" 或 "**Move**"（复制/导入 或 移动）
     - **不要选** "Link"（链接）
   - **File Renaming**（文件重命名）：可以启用或禁用
   - **Subfolder Structure**（子文件夹结构）：保持默认

#### 4.2 批量关联并复制PDF

1. 在Zotero中选择一个集合（例如"drug_screening"）
2. 按 Ctrl+A 选择所有条目
3. 右键点击 → ZotMoov → "**Attach from Source Folder**"
4. ZotMoov会：
   - 在源文件夹中查找匹配的PDF文件
   - **复制**PDF到Zotero存储目录（因为我们设置了Copy模式）
   - 将附件关联到条目
5. 重复步骤1-4，处理所有集合

### 第5步：验证PDF已复制

1. 选择任意一个有PDF附件的条目
2. 右键点击附件 → "Show File"（显示文件）
3. 确认文件路径在Zotero存储目录下：
   ```
   /home/shuifeng/Zotero/storage/XXXXXXXX/filename.pdf
   ```
   而不是U盘路径：
   ```
   /media/shuifeng/BEA6-BBCE/pdfs/filename.pdf
   ```

4. 完成后，可以安全地卸载U盘

## 备选方案：手动批量操作

如果ZotMoov配置复杂，可以使用Zotero内置功能：

### 方法：拖放复制

1. 打开文件管理器，导航到：`/media/shuifeng/BEA6-BBCE/pdfs`
2. 打开Zotero，选择要添加PDF的条目
3. **按住Shift键**，将PDF文件从文件管理器拖放到Zotero条目上
4. Shift+拖放会**复制**文件（不是链接）

缺点：需要手动匹配PDF和条目，适合小批量操作。

## 故障排除

### ZotMoov仍然创建链接而不是复制

检查：
1. ZotMoov Preferences → Attachment Method 是否设置为 "Copy" 或 "Import"
2. Destination Folder 是否正确设置为Zotero存储目录

### PDF无法找到

确保：
1. PDF文件名和条目标题匹配
2. 源文件夹路径正确：`/media/shuifeng/BEA6-BBCE/pdfs`
3. U盘已正确挂载

### 附件显示错误路径

如果附件路径显示为：
```
/home/shuifeng/snap/zotero-snap/common/Zotero/storage/XXXXXXXX/_media_shuifeng_BEA6-BBCE_pdfs_...
```

这说明ZotMoov在链接模式下运行。需要：
1. 删除所有附件
2. 重新配置ZotMoov为复制模式
3. 重新运行"Attach from Source Folder"

## 预期结果

完成后，您应该有：
- 163条文献元数据，分布在10个集合中
- 每条文献都有对应的PDF附件（如果源文件存在）
- 所有PDF文件存储在Zotero存储目录：
  ```
  /home/shuifeng/Zotero/storage/
  或
  /home/shuifeng/snap/zotero-snap/common/Zotero/storage/
  ```
- 可以安全卸载U盘，附件仍然可访问

## 快速命令参考

```bash
# 重新导入元数据（如果需要）
cd /home/shuifeng/Claude_code/001.zotera_create_ris/zotero_restoren_from_endnote
python3 auto_import_zotero.py

# 检查RIS文件
ls -lh outputs2/out_ris_class/

# 检查PDF文件
ls -lh /media/shuifeng/BEA6-BBCE/pdfs/ | wc -l
```

## 下一步行动清单

- [ ] 1. 在Zotero GUI中删除所有测试集合
- [ ] 2. 运行 `python3 auto_import_zotero.py` 导入元数据
- [ ] 3. 打开ZotMoov Preferences，配置为复制模式
- [ ] 4. 对每个集合运行"Attach from Source Folder"
- [ ] 5. 验证PDF已复制到Zotero存储目录
- [ ] 6. 卸载U盘并测试附件可访问性
