#!/usr/bin/env python3
"""
从单个RIS文件合并为分类RIS（移除L1附件字段）
每个类别一个RIS文件，方便Zotero导入
"""

from pathlib import Path
import json


def merge_ris_by_category_no_attachment(input_dir, output_dir):
    """
    按类别合并RIS文件，移除附件字段

    输出：每个类别一个RIS文件
    例如：Multi-Omics.ris (包含5条记录，无附件字段)
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"正在合并RIS文件（移除附件字段）...\n")

    total_categories = 0
    total_records = 0

    # 遍历每个类别文件夹
    for cat_dir in sorted(input_dir.iterdir()):
        if not cat_dir.is_dir():
            continue

        cat_name = cat_dir.name
        ris_files = list(cat_dir.glob("*.ris"))

        if not ris_files:
            continue

        total_categories += 1
        merged_records = []

        # 读取该类别下的所有RIS文件
        for ris_file in ris_files:
            with open(ris_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            # 移除L1字段（本地附件路径）
            lines = []
            for line in content.split('\n'):
                if not line.startswith('L1  - '):
                    lines.append(line)

            clean_content = '\n'.join(lines)
            if clean_content:
                merged_records.append(clean_content)

        # 写入合并的RIS文件
        if merged_records:
            output_file = output_dir / f"{cat_name}.ris"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(merged_records))
                f.write('\n')

            total_records += len(merged_records)
            print(f"✓ {cat_name}.ris - {len(merged_records)} 条记录")

    print(f"\n完成!")
    print(f"  类别数: {total_categories}")
    print(f"  总记录数: {total_records}")
    print(f"  输出目录: {output_dir}")
    print(f"\n使用方法:")
    print(f"  1. File → Import")
    print(f"  2. 选择一个类别的RIS文件（如Multi-Omics.ris）")
    print(f"  3. 导入成功后，使用ZotMoov批量关联PDF")
    print(f"  4. 重复步骤1-3导入其他类别")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='合并RIS文件（每个类别一个文件，无附件字段）'
    )
    parser.add_argument(
        '--input',
        default='outputs2/out_ris_by_category',
        help='输入目录（包含分类子目录）'
    )
    parser.add_argument(
        '--output',
        default='outputs2/out_ris_merged_no_attachment',
        help='输出目录'
    )

    args = parser.parse_args()

    merge_ris_by_category_no_attachment(args.input, args.output)
