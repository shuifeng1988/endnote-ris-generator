# 全自动导入Zotero - 完整指南

## 🎯 这才是真正的自动化！

**一个命令，完成所有操作**：
- ✅ 自动创建集合（按分类）
- ✅ 自动导入元数据（标题、作者、DOI等）
- ✅ 自动关联PDF附件
- ✅ 无需任何手动操作！

---

## 🚀 快速开始（5分钟设置，然后全自动）

### 第一步：获取Zotero API凭证（只需一次）

1. **访问Zotero设置页面**
   ```
   https://www.zotero.org/settings/keys
   ```

2. **创建API Key**
   - 点击 "Create new private key"
   - Key名称：随便写（如"Auto Import"）
   - 权限设置：
     * ✅ Personal Library: **Allow library access** (Read/Write)
     * ✅ **Allow notes access**
     * ✅ **Allow write access**
     * ❌ Default Group Permissions: None
   - 点击 "Save Key"
   - **复制显示的API Key**（只显示一次！）

3. **找到Library ID**
   - 在同一页面顶部，找到：
     ```
     Your userID for use in API calls is XXXXXX
     ```
   - 这个XXXXXX就是你的Library ID

### 第二步：运行全自动导入

```bash
# 确保安装了依赖
pip install pyzotero

# 运行自动导入（会提示输入API凭证）
python3 auto_import_zotero.py
```

**首次运行会询问**：
```
请输入 Library ID: [输入你的Library ID]
请输入 API Key: [粘贴你的API Key]
Library类型 (user/group) [user]: [直接回车]
是否保存配置? (y/n) [n]: y  [输入y保存，下次不用再输入]
```

**然后脚本会自动**：
1. 读取所有13个分类的RIS文件
2. 在Zotero中创建对应的集合
3. 逐个导入每条文献（124条）
4. 自动查找并关联PDF文件

---

## 📊 预期输出示例

```
======================================================================
全自动导入开始
======================================================================
RIS目录: outputs2/out_ris_merged_no_attachment
PDF目录: /media/shuifeng/BEA6-BBCE/pdfs
类别数: 13
======================================================================

======================================================================
导入类别: Multi-Omics
======================================================================
  ✓ 创建集合: Multi-Omics
  找到 5 条记录
  ✓ A Multi-Omics Framework for Decoding Disease... [附件: ✓]
  ✓ Deep learning models reading clinical data... [附件: ✓]
  ✓ Applications of multi-omics analysis in human... [附件: ✓]
  ✓ ggkegg: analysis and visualization of KEGG... [附件: ✓]
  ✓ Multi-omics landscape and molecular basis... [附件: ✓]

总结:
  成功导入: 5/5
  关联PDF: 5/5

======================================================================
导入类别: Drug-Screening
======================================================================
  集合已存在: Drug-Screening
  找到 15 条记录
  ✓ Connectivity Map: Using Gene-Expression... [附件: ✓]
  ...

[继续处理其他11个类别...]

======================================================================
全部导入完成！
======================================================================
```

---

## ⚡ 高级用法

### 只导入特定类别（测试用）

```bash
# 先测试Multi-Omics（只有5条记录）
python3 auto_import_zotero.py --category Multi-Omics

# 检查Zotero，如果成功再导入其他类别
python3 auto_import_zotero.py --category Drug-Screening
```

### 使用命令行参数（跳过交互式输入）

```bash
python3 auto_import_zotero.py \
  --library-id YOUR_LIBRARY_ID \
  --api-key YOUR_API_KEY \
  --ris-dir outputs2/out_ris_merged_no_attachment \
  --pdf-dir /media/shuifeng/BEA6-BBCE/pdfs
```

### 指定不同的PDF目录

```bash
python3 auto_import_zotero.py --pdf-dir /path/to/your/pdfs
```

---

## 🔍 工作原理

### PDF关联策略

脚本使用**多重匹配策略**自动查找PDF：

1. **从RIS的N1字段提取路径**（如果有）
   ```
   N1  - attachments=file:///path/to/paper.pdf
   ```

2. **按文件名模糊匹配**
   - 使用标题的前30个字符
   - 在PDF目录中查找包含该字符串的文件

3. **按DOI匹配**（未来可扩展）
   - 读取PDF内容查找DOI
   - 根据DOI匹配

### API操作流程

```
读取RIS文件 → 解析元数据 → 创建Zotero集合
→ 创建文献条目 → 查找PDF文件 → 关联附件
```

---

## 🛠️ 故障排除

### 问题1：API连接失败

**错误信息**：
```
错误: 无法连接到Zotero API
```

**解决方法**：
1. 检查Library ID和API Key是否正确
2. 确认API Key有"Write access"权限
3. 检查网络连接
4. 确认Zotero服务器可访问（https://api.zotero.org）

### 问题2：附件关联失败

**可能原因**：
- PDF文件路径不正确
- 文件名与标题差异太大
- 文件权限问题

**解决方法**：
```bash
# 检查PDF文件存在
ls -la /media/shuifeng/BEA6-BBCE/pdfs/ | head

# 检查文件权限
chmod 644 /media/shuifeng/BEA6-BBCE/pdfs/*.pdf
```

### 问题3：重复导入

**说明**：脚本会检查集合是否已存在，但不会检查条目是否重复。

**解决方法**：
- 首次导入前，确保Zotero中没有同名集合
- 或者手动删除已有集合后重新导入

---

## 📈 性能预期

- **处理速度**：约2-5条/秒（取决于网络速度）
- **124条文献**：约1-3分钟全部完成
- **完全自动**：无需任何手动操作

---

## 🎉 对比之前的方案

| 方案 | 自动化程度 | 操作次数 | 耗时 |
|------|-----------|---------|------|
| 手动拖放单个RIS | ❌ 0% | 138次 | 2小时+ |
| 导入合并RIS + ZotMoov | ⚠️ 50% | 13次导入 + 13次关联 | 30分钟 |
| **API自动导入** | ✅ 100% | **1次** | **3分钟** |

---

## ✅ 立即开始

```bash
# 1. 获取API凭证（访问链接）
https://www.zotero.org/settings/keys

# 2. 运行脚本
python3 auto_import_zotero.py

# 3. 输入Library ID和API Key

# 4. 等待3分钟...

# 5. 完成！打开Zotero查看结果
```

---

## 💾 配置文件说明

首次运行后，如果选择保存配置，会生成 `.zotero_config.json`：

```json
{
  "library_id": "123456",
  "api_key": "xxxxxxxxxxxx",
  "library_type": "user"
}
```

下次运行会自动读取，无需再次输入。

**安全提示**：不要将此文件提交到Git仓库！

---

需要帮助？运行：
```bash
python3 auto_import_zotero.py --help
```
