# EndNote RIS Generator / EndNote RIS 生成工具

[English](README_EN.md) | [中文](README_CN.md)

---

## Quick Links / 快速链接

- **English Documentation**: [README_EN.md](README_EN.md)
- **中文文档**: [README_CN.md](README_CN.md)

---

## Overview / 概述

A powerful, AI-driven tool for generating EndNote and Zotero-compatible RIS files from various document formats and directory structures.

一款强大的 AI 驱动工具，可从各种文档格式和目录结构生成 EndNote 和 Zotero 兼容的 RIS 文件。

---

## Key Features / 主要特性

- 📂 **Multi-Format Support** / **多格式支持**: PDF, Word, PowerPoint, Excel, Text
- 🔄 **EndNote Library Recovery** / **EndNote 库恢复**: Rescue corrupted libraries
- 🤖 **AI-Powered Extraction** / **AI 驱动提取**: Intelligent metadata extraction
- 🔍 **Advanced OCR** / **高级 OCR**: Vision LLM & Tesseract modes
- 🗂️ **Auto-Classification** / **自动分类**: User-defined categories
- 🔗 **Smart Supplement Merging** / **智能补充材料合并**: Automatic detection and linking
- ⚡ **High Performance** / **高性能**: Concurrent processing support
- 🎯 **Cross-Platform** / **跨平台**: EndNote & Zotero compatible

---

## Quick Start / 快速开始

### Installation / 安装

```bash
pip install -r requirements.txt
```

### Basic Usage / 基础用法

```bash
# Use default configuration / 使用默认配置
python endnote_cli.py create --enable_ocr --ocr_lang eng+chi_sim

# With auto-classification / 带自动分类
python endnote_cli.py create \
  --enable_ocr \
  --ocr_lang eng+chi_sim \
  --auto_classify \
  --num_categories 10 \
  --merge_supplements
```

---

## Documentation / 文档

For detailed documentation, please refer to:

详细文档请参考：

- **English**: [README_EN.md](README_EN.md)
- **中文**: [README_CN.md](README_CN.md)

---

## License / 许可证

MIT License

---

## Author / 作者

GitHub: [@shuifeng1988](https://github.com/shuifeng1988)
