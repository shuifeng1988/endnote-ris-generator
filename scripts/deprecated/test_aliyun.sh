#!/bin/bash
# 测试脚本 - 使用阿里云API处理10条记录

echo "🚀 开始测试 - 阿里云API (10条记录)"
echo "================================"
echo ""
echo "配置信息:"
echo "  主模型: qwen-plus (文本处理)"
echo "  OCR模型: qwen-vl-max (视觉识别)"
echo "  数据目录: /media/shuifeng/BEA6-BBCE/pdfs"
echo "  输出目录: ./outputs"
echo ""
echo "================================"
echo ""

# 运行程序
python3 zotero_restore_from_endnote_pdf_directories.py \
  --max_records 10 \
  --enable_ocr

echo ""
echo "================================"
echo "✅ 测试完成！"
echo ""
echo "查看结果:"
echo "  输出文件: ls outputs/out_ris/"
echo "  中间文件: ls outputs/out_intermediate/"
echo "  日志文件: tail -f outputs/logs/*.log"
echo "  验证质量: python3 validate_output.py outputs/out_intermediate"
echo ""
