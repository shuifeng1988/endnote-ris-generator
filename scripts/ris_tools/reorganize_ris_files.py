#!/usr/bin/env python3
"""
从现有的合并RIS文件反向提取，按类别组织单个RIS文件
解决Zotero导入多记录RIS时附件无法显示的问题
"""

import json
import shutil
from pathlib import Path


def extract_and_organize_from_merged(
    merged_class_dir,
    original_ris_dir,
    output_base_dir
):
    """
    从合并的RIS文件中提取信息，并组织原始单个RIS文件到类别文件夹

    Args:
        merged_class_dir: 包含合并RIS的目录 (out_ris_class)
        original_ris_dir: 原始单个RIS文件目录 (out_ris)
        output_base_dir: 输出基目录
    """
    merged_class_dir = Path(merged_class_dir)
    original_ris_dir = Path(original_ris_dir)
    output_base_dir = Path(output_base_dir)

    # 读取分类报告
    report_path = merged_class_dir / "classification_report.json"
    if not report_path.exists():
        print(f"错误: 找不到分类报告: {report_path}")
        return

    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)

    total_docs = report.get('total_documents', report.get('total_records', 0))
    print(f"找到分类报告: {total_docs} 条记录，{len(report['categories'])} 个类别")

    # 创建输出目录
    output_dir = output_base_dir / "out_ris_by_category"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 读取合并文件并提取记录标题，用于匹配原始文件
    category_records = {}

    for cat_info in report['categories']:
        cat_name = cat_info['name']
        merged_file = merged_class_dir / f"{cat_name}.ris"

        if not merged_file.exists():
            print(f"警告: 合并文件不存在: {merged_file}")
            continue

        # 读取合并文件，提取每条记录的标题
        with open(merged_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 按ER  -分割记录
        records = []
        for part in content.split('ER  -'):
            part = part.strip()
            if not part or 'TI  -' not in part:
                continue

            # 提取标题
            for line in part.split('\n'):
                if line.startswith('TI  - '):
                    title = line[6:].strip()
                    records.append(title)
                    break

        category_records[cat_name] = records
        print(f"类别 '{cat_name}': {len(records)} 条记录")

    # 现在遍历原始RIS文件，根据标题匹配到类别
    original_files = list(original_ris_dir.glob("*.ris"))
    print(f"\n处理 {len(original_files)} 个原始RIS文件...")

    # 创建标题到文件名的映射
    title_to_file = {}
    for ris_file in original_files:
        with open(ris_file, 'r', encoding='utf-8') as f:
            content = f.read()
            for line in content.split('\n'):
                if line.startswith('TI  - '):
                    title = line[6:].strip()
                    title_to_file[title] = ris_file.name
                    break

    # 按类别复制文件
    total_copied = 0
    for cat_name, titles in category_records.items():
        # 创建类别目录
        cat_dir = output_dir / cat_name
        cat_dir.mkdir(parents=True, exist_ok=True)

        copied = 0
        for title in titles:
            filename = title_to_file.get(title)
            if filename:
                src = original_ris_dir / filename
                dst = cat_dir / filename
                try:
                    shutil.copy2(src, dst)
                    copied += 1
                    total_copied += 1
                except Exception as e:
                    print(f"  错误: 无法复制 {filename}: {e}")
            else:
                print(f"  警告: 找不到标题对应的文件: {title[:50]}...")

        print(f"✓ {cat_name}: 复制了 {copied}/{len(titles)} 个文件到 {cat_dir}")

    print(f"\n完成! 总共复制了 {total_copied} 个文件")
    print(f"输出目录: {output_dir}")
    print(f"\n使用方法:")
    print(f"  1. 打开Zotero")
    print(f"  2. 为每个类别创建一个集合（Collection）")
    print(f"  3. 将对应类别文件夹中的所有RIS文件拖入该集合")
    print(f"  4. 所有附件应该都能正常显示！")

    # 复制分类报告
    shutil.copy2(report_path, output_dir / "classification_report.json")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='从合并RIS重新组织为单个文件（解决Zotero附件问题）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用默认路径
  python reorganize_ris_files.py

  # 指定自定义路径
  python reorganize_ris_files.py \\
    --merged outputs2/out_ris_class \\
    --original outputs2/out_ris \\
    --output outputs2
        """
    )

    parser.add_argument(
        '--merged',
        type=str,
        default='outputs2/out_ris_class',
        help='合并RIS文件目录（默认: outputs2/out_ris_class）'
    )
    parser.add_argument(
        '--original',
        type=str,
        default='outputs2/out_ris',
        help='原始单个RIS文件目录（默认: outputs2/out_ris）'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='outputs2',
        help='输出基目录（默认: outputs2）'
    )

    args = parser.parse_args()

    extract_and_organize_from_merged(
        args.merged,
        args.original,
        args.output
    )
