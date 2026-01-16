#!/usr/bin/env python3
"""
从out_ris_class的合并RIS文件移除附件字段
适用于已经合并的RIS文件（主程序的分类输出）
"""

from pathlib import Path


def remove_attachments_from_merged_ris(input_dir, output_dir):
    """
    读取已合并的RIS文件，移除L1附件字段

    Args:
        input_dir: 包含合并RIS的目录（如 out_ris_class）
        output_dir: 输出目录（out_ris_merged_no_attachment）
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"正在处理RIS文件（移除附件字段）...")
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}\n")

    if not input_dir.exists():
        print(f"错误: 输入目录不存在: {input_dir}")
        return

    # 查找所有RIS文件
    ris_files = list(input_dir.glob("*.ris"))

    if not ris_files:
        print(f"错误: 未找到RIS文件")
        return

    total_categories = 0
    total_records = 0

    for ris_file in sorted(ris_files):
        if ris_file.stem == 'classification_report':
            continue  # 跳过报告文件（如果有）

        with open(ris_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 移除L1字段
        lines = []
        for line in content.split('\n'):
            if not line.startswith('L1  - '):
                lines.append(line)

        clean_content = '\n'.join(lines)

        # 写入输出文件
        output_file = output_dir / ris_file.name
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(clean_content)

        # 统计记录数
        record_count = content.count('ER  -')
        total_records += record_count
        total_categories += 1

        print(f"✓ {ris_file.name} - {record_count} 条记录")

    print(f"\n完成!")
    print(f"  类别数: {total_categories}")
    print(f"  总记录数: {total_records}")
    print(f"  输出目录: {output_dir}")
    print(f"\n下一步:")
    print(f"  python3 auto_import_zotero.py")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='从合并的RIS文件移除附件字段'
    )
    parser.add_argument(
        '--input',
        default='outputs2/out_ris_class',
        help='输入目录（默认: outputs2/out_ris_class）'
    )
    parser.add_argument(
        '--output',
        default='outputs2/out_ris_merged_no_attachment',
        help='输出目录（默认: outputs2/out_ris_merged_no_attachment）'
    )

    args = parser.parse_args()

    remove_attachments_from_merged_ris(args.input, args.output)
