# EndNote 导入完整解决方案

从 Zotero 迁移到 EndNote 的完整指南，确保附件能够正确导入并可迁移。

## 目录

1. [问题说明](#问题说明)
2. [解决方案](#解决方案)
3. [工具使用](#工具使用)
4. [完整流程](#完整流程)
5. [常见问题](#常见问题)

---

## 问题说明

### 主要问题

1. **RIS 附件路径问题**：
   - Zotero 导出的 RIS 文件中，附件路径可能是 Zotero 内部格式（如 `storage:XXXXX/file.pdf`）
   - EndNote 无法识别这种路径格式
   - 导入时附件不会被复制到 EndNote 库中

2. **JSON 格式错误**：
   - 导出或转换过程中可能出现 JSON 格式错误
   - 手动查找和修复规则非常耗时
   - 需要自动化的修复方案

### EndNote 附件导入要求

EndNote 导入附件需要满足以下条件：

1. **路径格式**：使用 `L1` 字段指定附件路径
2. **路径类型**：
   - 相对路径：相对于 RIS 文件的位置（推荐）
   - 绝对路径：完整的文件系统路径
3. **文件可访问**：附件文件必须存在且可访问
4. **导入设置**：EndNote 导入时需要选择 "Copy files to library folder"

---

## 解决方案

本方案提供两个工具：

### 1. RIS 附件路径修复工具 (`fix_ris_for_endnote.py`)

**功能**：
- 解析 RIS 文件，提取所有条目
- 查找每个条目对应的 PDF 附件
- 将 PDF 复制到统一的 `PDF` 文件夹
- 修复 RIS 文件中的附件路径为相对路径
- 生成 EndNote 可直接导入的 RIS 文件

**特点**：
- 自动匹配 PDF 文件（基于文件名、作者、年份、标题）
- 智能文件名生成（作者_年份_标题）
- 完整的统计信息
- 支持多个 PDF 搜索目录

### 2. JSON 格式自动修复工具 (`fix_json_with_ai.py`)

**功能**：
- 使用 AI 大模型自动识别和修复 JSON 格式错误
- 无需手动查找规则
- 支持各种常见 JSON 错误
- 自动备份原文件

**特点**：
- 使用阿里云通义千问模型（或其他 OpenAI 兼容 API）
- 智能错误定位
- 自动验证修复结果
- 支持大文件（自动截取错误附近内容）

---

## 工具使用

### 前置要求

```bash
# 安装依赖
pip install openai

# 配置 API（用于 JSON 修复工具）
# 编辑 .env 文件或设置环境变量
LLM_API_KEY=your_api_key
BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
MODEL=qwen-plus
```

### 工具 1：RIS 附件路径修复

#### 基本用法

```bash
# 修复 RIS 文件，在当前目录搜索 PDF
python fix_ris_for_endnote.py input.ris

# 指定输出文件名
python fix_ris_for_endnote.py input.ris -o my_library.ris

# 指定 PDF 搜索目录
python fix_ris_for_endnote.py input.ris -p /path/to/pdfs /another/path

# 指定输出目录
python fix_ris_for_endnote.py input.ris -d my_output_folder
```

#### 参数说明

- `input_ris`：输入的 RIS 文件路径（必需）
- `-o, --output`：输出的 RIS 文件名（默认：`fixed_library.ris`）
- `-d, --output-dir`：输出目录（默认：`endnote_ready`）
- `-p, --pdf-dirs`：PDF 搜索目录，可指定多个（默认：当前目录）

#### 输出结构

```
endnote_ready/
├── fixed_library.ris    # 修复后的 RIS 文件
└── PDF/                 # 所有附件 PDF
    ├── Author1_2023_Title1.pdf
    ├── Author2_2024_Title2.pdf
    └── ...
```

### 工具 2：JSON 格式自动修复

#### 基本用法

```bash
# 修复 JSON 文件（自动备份原文件）
python fix_json_with_ai.py input.json

# 指定输出文件
python fix_json_with_ai.py input.json -o output.json

# 不备份原文件
python fix_json_with_ai.py input.json --no-backup

# 指定 API 配置
python fix_json_with_ai.py input.json --api-key YOUR_KEY --model qwen-plus
```

#### 参数说明

- `input`：输入的 JSON 文件路径（必需）
- `-o, --output`：输出文件路径（默认：覆盖原文件）
- `--no-backup`：不备份原文件
- `--api-key`：API 密钥（也可通过环境变量 `LLM_API_KEY` 设置）
- `--base-url`：API 基础 URL（也可通过环境变量 `BASE_URL` 设置）
- `--model`：模型名称（也可通过环境变量 `MODEL` 设置）
- `--env-file`：.env 文件路径（默认：`.env`）

---

## 完整流程

### 方案 A：从 Zotero RIS 导出开始

如果你已经有 Zotero 导出的 RIS 文件：

```bash
# 1. 修复 RIS 文件和附件路径
python fix_ris_for_endnote.py zotero_export.ris -p /path/to/zotero/storage

# 2. 将 endnote_ready 文件夹复制到 Windows 系统

# 3. 在 Windows 的 EndNote 中导入：
#    - File → Import → File
#    - 选择 fixed_library.ris
#    - Import Option: RefMan (RIS)
#    - Duplicates: Import All
#    - 确保勾选 "Copy files to library folder"
```

### 方案 B：从 Zotero JSON 导出开始

如果你有 Zotero 导出的 JSON 文件：

```bash
# 1. 如果 JSON 格式有问题，先修复
python fix_json_with_ai.py zotero_export.json

# 2. 将 JSON 转换为 RIS（使用现有工具或 Zotero）
# 在 Zotero 中：File → Export Library → Format: RIS

# 3. 修复 RIS 文件
python fix_ris_for_endnote.py exported.ris -p /path/to/pdfs

# 4. 导入到 EndNote（同方案 A 步骤 2-3）
```

### 方案 C：直接从 Zotero 导出

最简单的方法：

```bash
# 1. 在 Zotero 中导出
#    - 选择要导出的文献
#    - File → Export Library
#    - Format: RIS
#    - 勾选 "Export Files"

# 2. 修复导出的 RIS
python fix_ris_for_endnote.py My\ Library.ris -p .

# 3. 导入到 EndNote
```

---

## 常见问题

### Q1: EndNote 导入后附件没有显示？

**可能原因**：
1. RIS 文件和 PDF 文件夹不在同一目录
2. EndNote 导入时没有选择 "Copy files to library folder"
3. 附件路径格式不正确

**解决方法**：
```bash
# 确保目录结构正确
endnote_ready/
├── fixed_library.ris
└── PDF/
    └── *.pdf

# 重新导入，确保选择正确的选项
```

### Q2: JSON 修复失败？

**可能原因**：
1. API 密钥未配置
2. 网络连接问题
3. JSON 文件损坏严重

**解决方法**：
```bash
# 检查 API 配置
cat .env

# 测试 API 连接
python -c "from openai import OpenAI; client = OpenAI(api_key='YOUR_KEY', base_url='YOUR_URL'); print(client.models.list())"

# 尝试手动修复部分内容后再用工具
```

### Q3: PDF 文件没有被找到？

**可能原因**：
1. PDF 搜索目录不正确
2. PDF 文件名与条目信息不匹配
3. PDF 文件不存在

**解决方法**：
```bash
# 指定正确的 PDF 目录
python fix_ris_for_endnote.py input.ris -p /correct/path/to/pdfs

# 检查 PDF 文件是否存在
find /path/to/pdfs -name "*.pdf" | head -10

# 查看统计信息，了解匹配情况
# 工具会输出详细的统计信息
```

### Q4: EndNote 导入时提示格式错误？

**可能原因**：
1. RIS 文件编码问题
2. RIS 文件格式不标准

**解决方法**：
```bash
# 检查文件编码
file -i fixed_library.ris

# 转换编码（如果需要）
iconv -f UTF-8 -t UTF-8 -c fixed_library.ris > fixed_library_clean.ris

# 在 EndNote 中尝试不同的导入选项
# Import Option: 尝试 "RefMan (RIS)" 或 "Reference Manager"
```

### Q5: 如何批量处理多个 RIS 文件？

```bash
# 使用 shell 脚本批量处理
for ris in *.ris; do
    python fix_ris_for_endnote.py "$ris" -o "fixed_$ris" -d "output_$(basename $ris .ris)"
done
```

### Q6: 附件文件名太长或包含特殊字符？

工具会自动处理：
- 清理非法字符（`< > : " / \ | ? *`）
- 限制文件名长度
- 使用安全的文件名格式（作者_年份_标题）

### Q7: 如何验证 EndNote 导入是否成功？

在 EndNote 中：
1. 检查导入的条目数量是否正确
2. 随机选择几个条目，点击附件图标查看 PDF
3. 检查 EndNote 库文件夹中的 PDF 文件夹
4. 确认 PDF 已被复制到库中（不是链接）

---

## 高级技巧

### 1. 自定义 PDF 文件名格式

编辑 `fix_ris_for_endnote.py` 中的 `_generate_pdf_filename` 方法：

```python
def _generate_pdf_filename(self, entry: Dict[str, List[str]], extension: str = '.pdf') -> str:
    # 自定义文件名格式
    # 例如：只使用标题
    title = ' '.join(entry.get('TI', ['untitled']))[:50]
    filename = title
    # ... 清理字符 ...
    return f"{filename}{extension}"
```

### 2. 使用本地 LLM 修复 JSON

如果你有本地部署的 LLM（如 Ollama）：

```bash
# 编辑 .env.ollama
LLM_API_KEY=ollama
BASE_URL=http://localhost:11434/v1
MODEL=qwen2.5:14b

# 使用本地模型
python fix_json_with_ai.py input.json --env-file .env.ollama
```

### 3. 批量验证 JSON 文件

```python
from fix_json_with_ai import JSONAutoFixer

fixer = JSONAutoFixer()
for json_file in Path('.').glob('*.json'):
    if not fixer.validate_json_file(json_file):
        print(f"需要修复: {json_file}")
        fixer.fix_json_file(json_file)
```

---

## 技术细节

### RIS 格式说明

EndNote 使用以下字段识别附件：

- `L1` - 主要附件路径（推荐）
- `L2` - 备用附件路径
- `L4` - 图片路径
- `file` - 通用文件路径（某些版本）

路径格式：
```
L1  - PDF/Author_2023_Title.pdf    # 相对路径（推荐）
L1  - C:\Full\Path\To\File.pdf     # 绝对路径（Windows）
L1  - /full/path/to/file.pdf       # 绝对路径（Linux/Mac）
```

### PDF 匹配算法

工具使用以下策略匹配 PDF：

1. **直接匹配**：RIS 中已有的文件路径
2. **文件名匹配**：基于 PDF 文件名
3. **智能匹配**：基于作者、年份、标题的模糊匹配

匹配优先级：
```
1. 精确文件名匹配
2. 作者+年份匹配
3. 标题关键词匹配
```

---

## 支持的格式

### 输入格式

- **RIS**：Zotero、Mendeley、EndNote 等导出的 RIS 文件
- **JSON**：Zotero JSON 导出格式
- **PDF**：任何标准 PDF 文件

### 输出格式

- **RIS**：EndNote 兼容的 RIS 格式
- **PDF**：复制到统一目录的 PDF 文件

---

## 许可和贡献

本工具集是开源的，欢迎贡献和改进。

### 已知限制

1. 不支持非 PDF 附件（如 Word、Excel 等）
2. 大文件 JSON 修复可能较慢
3. PDF 匹配可能不是 100% 准确

### 改进建议

如果你有改进建议或发现 bug，请：
1. 提交 Issue
2. 提供示例文件（去除敏感信息）
3. 描述预期行为和实际行为

---

## 总结

使用本工具集，你可以：

✅ 轻松将 Zotero 文献库迁移到 EndNote
✅ 确保所有附件正确导入并可迁移
✅ 自动修复 JSON 格式错误
✅ 节省大量手动处理时间

**关键步骤**：
1. 从 Zotero 导出 RIS
2. 使用 `fix_ris_for_endnote.py` 修复附件路径
3. 将输出文件夹复制到 Windows
4. 在 EndNote 中导入，确保选择 "Copy files to library folder"

祝你迁移顺利！🎉
