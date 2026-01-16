# 从目录生成 EndNote 可用的 RIS 文件

## 快速开始

这个脚本可以扫描一个目录（包含子目录），识别所有文档文件，并生成 EndNote 可以直接导入的 RIS 文件，附件使用相对路径。

### 基本用法

```bash
# 扫描目录并生成 RIS
python create_endnote_ris_from_directory.py /path/to/your/documents

# 指定输出目录
python create_endnote_ris_from_directory.py /path/to/your/documents --out_dir ./my_output
```

### 输出结构

```
output/
├── out_ris/              # RIS 文件（每个文档一个）
│   ├── file1_abc123.ris
│   ├── file2_def456.ris
│   └── ...
├── out_intermediate/     # 中间 JSON 文件（调试用）
│   ├── file1_abc123.json
│   └── ...
└── pdf/                  # 所有源文件（复制）
    ├── file1.pdf
    ├── file2.docx
    ├── subdir_file3.pdf  # 子目录文件会加上前缀
    └── ...
```

### 在 Windows 的 EndNote 中导入

1. **复制文件夹**
   - 将整个 `output` 文件夹复制到 Windows 系统

2. **批量导入 RIS**
   - 打开 EndNote
   - File → Import → File
   - 浏览到 `output/out_ris` 目录
   - 选择所有 `.ris` 文件（Ctrl+A 全选）
   - Import Option: 选择 **RefMan (RIS)**
   - Duplicates: 选择 **Import All** 或 **Discard Duplicates**
   - **重要**：确保勾选 **"Copy files to library folder"**

3. **验证导入**
   - EndNote 会自动识别 `./pdf/` 路径
   - 附件会被复制到 EndNote 库中
   - 点击任意条目的附件图标，应该能打开 PDF

## 支持的文件格式

- PDF (`.pdf`)
- Word (`.doc`, `.docx`)
- PowerPoint (`.ppt`, `.pptx`)
- Excel (`.xls`, `.xlsx`)
- 文本 (`.txt`, `.rtf`, `.odt`)
- 电子书 (`.epub`, `.mobi`)
- 其他 (`.djvu`, `.ps`, `.eps`)

## 高级选项

### 不递归扫描子目录

```bash
python create_endnote_ris_from_directory.py /path/to/documents --no-recursive
```

### 不包含根目录文件

```bash
python create_endnote_ris_from_directory.py /path/to/documents --no-root-files
```

### 调整并发数

```bash
# 使用 8 个线程并发处理
python create_endnote_ris_from_directory.py /path/to/documents --max-workers 8

# 单线程模式（调试用）
python create_endnote_ris_from_directory.py /path/to/documents --max-workers 1
```

## 工作原理

### 1. 文件扫描
- 递归扫描指定目录
- 识别所有支持的文件格式
- 保留子目录结构信息

### 2. 元数据提取
- 从文件名提取基本信息（标题、作者、年份）
- 常见格式：
  - `Author_2023_Title.pdf`
  - `Title (2023).pdf`
  - `[2023] Author - Title.pdf`

### 3. 附件处理
- 复制所有文件到 `output/pdf/` 目录
- 子目录文件名会加上路径前缀（如 `subdir_file.pdf`）
- RIS 中使用相对路径：`./pdf/filename.pdf`

### 4. RIS 生成
- 每个文件生成一个独立的 RIS 文件
- 使用 `L1` 字段指定附件路径
- EndNote 会根据相对路径自动查找附件

## 为什么使用相对路径？

### 相对路径的优势

1. **可移植性**：整个 `output` 文件夹可以在不同系统间复制
2. **兼容性**：EndNote 在 Windows 下能正确识别 `./pdf/` 格式
3. **自动复制**：导入时 EndNote 会自动将附件复制到库中

### 路径格式说明

```
RIS 文件位置：output/out_ris/file1.ris
附件位置：    output/pdf/file1.pdf
相对路径：    ./pdf/file1.pdf
```

在 Windows 导入时：
- EndNote 从 RIS 文件的位置开始查找
- `./pdf/file1.pdf` 表示：当前目录的父目录下的 `pdf` 文件夹
- 实际上，只要 `pdf` 文件夹和 `out_ris` 文件夹在同一父目录下即可

## 与 Zotero 脚本的区别

| 特性 | zotero_restore_from_endnote_pdf_directories.py | create_endnote_ris_from_directory.py |
|------|-----------------------------------------------|-------------------------------------|
| 目标 | 从 EndNote 目录恢复到 Zotero | 从任意目录生成 EndNote RIS |
| 附件路径 | `file://` URI（绝对路径） | `./pdf/` 相对路径 |
| AI 提取 | 支持（使用 LLM 提取元数据） | 可选（暂未实现） |
| OCR | 支持 | 不支持 |
| 分类 | 支持自动分类 | 不支持 |
| 用途 | Zotero 恢复 | EndNote 导入 |

## 常见问题

### Q1: EndNote 导入后找不到附件？

**检查清单**：
1. 确保 `output` 文件夹完整复制到 Windows
2. 确保 `pdf` 文件夹和 `out_ris` 文件夹在同一父目录
3. 导入时确保勾选了 "Copy files to library folder"
4. 检查 EndNote 的导入日志（File → Import → Show Import Log）

### Q2: 子目录中的文件会丢失吗？

不会。子目录中的文件会：
1. 被复制到 `output/pdf/` 目录
2. 文件名会加上子目录前缀（如 `subdir_file.pdf`）
3. RIS 中正确引用

### Q3: 如何批量导入所有 RIS 文件？

在 EndNote 中：
1. File → Import → File
2. 浏览到 `output/out_ris` 目录
3. 按 `Ctrl+A` 全选所有 `.ris` 文件
4. 点击 Open
5. EndNote 会依次导入所有文件

### Q4: 可以在 Linux/Mac 上生成，在 Windows 上导入吗？

可以！这正是这个脚本的设计目的：
1. 在 Linux/Mac 上运行脚本生成 RIS
2. 将 `output` 文件夹复制到 Windows
3. 在 Windows 的 EndNote 中导入

相对路径 `./pdf/` 在所有系统上都能正确工作。

### Q5: 如何验证 RIS 文件格式是否正确？

```bash
# 查看生成的 RIS 文件
cat output/out_ris/file1_abc123.ris

# 应该看到类似内容：
# TY  - GEN
# TI  - Document Title
# AU  - Author Name
# PY  - 2023
# L1  - ./pdf/file1.pdf
# ER  -
```

### Q6: 文件名中有特殊字符怎么办？

脚本会自动处理：
- 空格、斜杠等会被替换为下划线
- 保证文件名在 Windows 下有效
- 原始路径信息保存在 RIS 的 `N1` 备注字段中

## 示例

### 示例 1：简单目录

```bash
# 输入目录结构
documents/
├── Paper1.pdf
├── Paper2.pdf
└── Paper3.pdf

# 运行脚本
python create_endnote_ris_from_directory.py documents

# 输出
output/
├── out_ris/
│   ├── Paper1_abc123.ris
│   ├── Paper2_def456.ris
│   └── Paper3_ghi789.ris
└── pdf/
    ├── Paper1.pdf
    ├── Paper2.pdf
    └── Paper3.pdf
```

### 示例 2：带子目录

```bash
# 输入目录结构
documents/
├── 2023/
│   ├── Paper1.pdf
│   └── Paper2.pdf
└── 2024/
    └── Paper3.pdf

# 运行脚本
python create_endnote_ris_from_directory.py documents

# 输出
output/
├── out_ris/
│   ├── Paper1_abc123.ris
│   ├── Paper2_def456.ris
│   └── Paper3_ghi789.ris
└── pdf/
    ├── 2023_Paper1.pdf
    ├── 2023_Paper2.pdf
    └── 2024_Paper3.pdf
```

### 示例 3：混合文件类型

```bash
# 输入目录结构
documents/
├── Paper1.pdf
├── Presentation.pptx
└── Data.xlsx

# 运行脚本
python create_endnote_ris_from_directory.py documents

# 输出
output/
├── out_ris/
│   ├── Paper1_abc123.ris
│   ├── Presentation_def456.ris
│   └── Data_ghi789.ris
└── pdf/
    ├── Paper1.pdf
    ├── Presentation.pptx
    └── Data.xlsx
```

## 技术细节

### RIS 格式

生成的 RIS 文件格式：

```
TY  - GEN                    # 文献类型（Generic）
TI  - Document Title         # 标题
AU  - Author Name            # 作者
PY  - 2023                   # 年份
N1  - Source: path/to/file   # 备注（原始路径）
L1  - ./pdf/filename.pdf     # 附件路径（相对路径）
ER  -                        # 结束标记
```

### 文件 ID 生成

每个文件生成唯一 ID（SHA1 哈希）：
- 基于文件路径、大小、修改时间
- 用于生成唯一的输出文件名
- 避免文件名冲突

### 并发处理

- 默认使用 4 个线程并发处理
- 适合处理大量文件
- 线程安全的进度计数

## 未来改进

- [ ] 集成 AI 元数据提取（使用 LLM）
- [ ] 支持 OCR（扫描版 PDF）
- [ ] 支持从 PDF 中提取 DOI
- [ ] 支持自动分类
- [ ] 支持增量更新（只处理新文件）

## 总结

这个脚本的核心优势：

✅ **简单易用**：一条命令生成所有 RIS
✅ **跨平台**：Linux/Mac 生成，Windows 导入
✅ **相对路径**：可移植，EndNote 能正确识别
✅ **批量处理**：支持大量文件并发处理
✅ **完整迁移**：附件自动复制到 EndNote 库

现在你可以轻松地将任何目录中的文档导入到 EndNote 中！
