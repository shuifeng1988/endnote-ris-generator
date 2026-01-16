#!/usr/bin/env python3
"""
修复合并RIS文件的附件问题
解决Zotero导入多条记录RIS文件时无法显示附件的问题
"""

import sys
import re
from pathlib import Path
from urllib.parse import unquote


def fix_ris_file(input_path, output_path=None, mode='absolute'):
    """
    修复RIS文件的附件字段

    Args:
        input_path: 输入RIS文件路径
        output_path: 输出RIS文件路径（如果为None，覆盖原文件）
        mode: 修复模式
            - 'absolute': 保持绝对路径，但确保格式正确
            - 'linked': 使用Zotero链接附件格式（L2字段）
            - 'separate': 将L1和N1附件信息分离为独立字段
    """
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_fixed{input_path.suffix}"
    else:
        output_path = Path(output_path)

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按记录分割（以ER  -为分隔符）
    records = content.split('ER  -\n')
    fixed_records = []

    for record in records:
        if not record.strip():
            continue

        lines = record.split('\n')
        fixed_lines = []
        l1_path = None

        for line in lines:
            if line.startswith('L1  - '):
                # 提取L1字段的附件路径
                l1_path = line[6:].strip()

                if mode == 'absolute':
                    # 保持绝对路径，确保格式正确
                    fixed_lines.append(line)

                elif mode == 'linked':
                    # 转换为L2字段（URL格式）
                    # Zotero更容易识别L2字段作为链接附件
                    fixed_lines.append(f"L2  - {l1_path}")

                elif mode == 'separate':
                    # 保留L1，同时添加L4字段（PDF附件）
                    fixed_lines.append(line)
                    # 解码URL编码的路径
                    decoded_path = unquote(l1_path.replace('file:///', '/'))
                    fixed_lines.append(f"L4  - {decoded_path}")
            else:
                fixed_lines.append(line)

        # 重新组合记录
        fixed_record = '\n'.join(fixed_lines)
        fixed_records.append(fixed_record)

    # 合并所有记录，确保记录之间有空行
    output_content = 'ER  -\n\nTY  - JOUR\n'.join(fixed_records)
    # 添加最后的ER标记
    if not output_content.endswith('ER  -\n'):
        output_content += 'ER  -\n'

    # 修正第一个记录前的额外TY
    output_content = output_content.replace('ER  -\n\nTY  - JOUR\n', 'ER  -\n\n', 1)
    output_content = 'TY  - JOUR\n' + output_content.split('TY  - JOUR\n', 1)[1] if 'TY  - JOUR\n' in output_content else output_content

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_content)

    print(f"✓ 修复完成: {output_path}")
    print(f"  模式: {mode}")
    print(f"  记录数: {len([r for r in fixed_records if r.strip()])}")

    return output_path


def fix_all_merged_ris_files(class_dir, mode='absolute'):
    """
    批量修复分类目录中的所有RIS文件

    Args:
        class_dir: 包含分类RIS文件的目录
        mode: 修复模式
    """
    class_dir = Path(class_dir)
    if not class_dir.exists():
        print(f"错误: 目录不存在: {class_dir}")
        return

    ris_files = list(class_dir.glob("*.ris"))
    if not ris_files:
        print(f"警告: 未找到RIS文件: {class_dir}")
        return

    print(f"\n找到 {len(ris_files)} 个RIS文件")
    print(f"修复模式: {mode}\n")

    for ris_file in ris_files:
        if '_fixed' in ris_file.stem:
            continue  # 跳过已修复的文件
        try:
            fix_ris_file(ris_file, mode=mode)
        except Exception as e:
            print(f"✗ 错误: {ris_file.name} - {e}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='修复合并RIS文件的附件问题',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 修复单个文件（绝对路径模式）
  python fix_merged_ris_attachments.py -f Multi-Omics.ris

  # 修复单个文件（链接附件模式，推荐）
  python fix_merged_ris_attachments.py -f Multi-Omics.ris -m linked

  # 批量修复目录中的所有RIS文件
  python fix_merged_ris_attachments.py -d outputs2/out_ris_class -m linked

  # 修复并指定输出文件
  python fix_merged_ris_attachments.py -f input.ris -o output.ris

修复模式说明:
  absolute: 保持绝对路径（默认）
  linked:   使用L2字段（Zotero链接附件，推荐）
  separate: 分离为L1和L4字段
        """
    )

    parser.add_argument('-f', '--file', type=str, help='要修复的RIS文件')
    parser.add_argument('-o', '--output', type=str, help='输出文件路径（可选）')
    parser.add_argument('-d', '--directory', type=str, help='批量修复目录中的所有RIS文件')
    parser.add_argument('-m', '--mode', type=str, default='absolute',
                       choices=['absolute', 'linked', 'separate'],
                       help='修复模式（默认: absolute）')

    args = parser.parse_args()

    if args.file:
        fix_ris_file(args.file, args.output, args.mode)
    elif args.directory:
        fix_all_merged_ris_files(args.directory, args.mode)
    else:
        parser.print_help()
        print("\n错误: 必须指定 -f 或 -d 参数")
        sys.exit(1)
