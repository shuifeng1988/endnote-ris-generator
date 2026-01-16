#!/usr/bin/env python3
"""
诊断工具：对比单个RIS和合并RIS的差异
找出为什么单个能显示附件，合并的不能
"""

import sys
from pathlib import Path


def analyze_ris_file(file_path):
    """分析RIS文件的结构"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 统计信息
    stats = {
        'file': Path(file_path).name,
        'total_bytes': len(content),
        'total_lines': len(content.split('\n')),
        'num_records': content.count('ER  -'),
        'has_l1': 'L1  -' in content,
        'has_l2': 'L2  -' in content,
        'has_n1': 'N1  -' in content,
        'l1_paths': [],
        'record_separators': []
    }

    # 提取所有L1路径
    for line in content.split('\n'):
        if line.startswith('L1  -'):
            stats['l1_paths'].append(line[6:].strip())

    # 检查记录分隔符
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.strip() == 'ER  -':
            # 检查后面是什么
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                stats['record_separators'].append(repr(next_line))

    return stats


def compare_single_vs_merged():
    """对比单个RIS和合并RIS"""
    # 分析一个单个RIS文件
    single_dir = Path('outputs2/out_ris')
    single_files = list(single_dir.glob('*.ris'))[:3]  # 取前3个

    # 分析一个合并RIS文件
    merged_file = Path('outputs2/out_ris_class/Multi-Omics_fixed.ris')

    print("=" * 70)
    print("对比分析：单个RIS vs 合并RIS")
    print("=" * 70)

    print("\n【单个RIS文件】")
    print("-" * 70)
    for f in single_files:
        stats = analyze_ris_file(f)
        print(f"\n文件: {stats['file']}")
        print(f"  记录数: {stats['num_records']}")
        print(f"  总行数: {stats['total_lines']}")
        print(f"  L1字段: {'有' if stats['has_l1'] else '无'}")
        if stats['l1_paths']:
            print(f"  附件路径: {stats['l1_paths'][0][:80]}...")
        if stats['record_separators']:
            print(f"  ER后的内容: {stats['record_separators']}")

    print("\n" + "=" * 70)
    print("【合并RIS文件】")
    print("-" * 70)
    if merged_file.exists():
        stats = analyze_ris_file(merged_file)
        print(f"\n文件: {stats['file']}")
        print(f"  记录数: {stats['num_records']}")
        print(f"  总行数: {stats['total_lines']}")
        print(f"  L1字段: {'有' if stats['has_l1'] else '无'}")
        print(f"  附件数: {len(stats['l1_paths'])}")
        if stats['l1_paths']:
            print(f"  第1条附件: {stats['l1_paths'][0][:80]}...")
        print(f"  记录分隔符情况: {len(stats['record_separators'])} 个ER标记")
        if stats['record_separators']:
            print(f"  ER后的行: {stats['record_separators'][:3]}")

        # 详细检查每个记录
        print("\n  详细记录分析:")
        with open(merged_file, 'r', encoding='utf-8') as f:
            content = f.read()
        records = content.split('\n\n')
        for i, rec in enumerate(records[:5], 1):
            has_ty = 'TY  -' in rec
            has_ti = 'TI  -' in rec
            has_l1 = 'L1  -' in rec
            has_er = 'ER  -' in rec
            print(f"    记录{i}: TY={'✓' if has_ty else '✗'} TI={'✓' if has_ti else '✗'} L1={'✓' if has_l1 else '✗'} ER={'✓' if has_er else '✗'}")


def extract_sample_records():
    """提取样本记录用于测试"""
    merged_file = Path('outputs2/out_ris_class/Multi-Omics_fixed.ris')
    if not merged_file.exists():
        print("找不到合并文件")
        return

    with open(merged_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取第一条记录
    first_record = content.split('\n\n')[0]
    if not first_record.endswith('ER  -'):
        first_record += '\nER  -'

    # 保存为单独的测试文件
    test_file = Path('outputs2/test_single_from_merged.ris')
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(first_record)
        f.write('\n')

    print(f"\n提取的测试文件: {test_file}")
    print("请用这个文件在Zotero中测试，看是否能显示附件")
    print(f"文件包含 {first_record.count('ER  -')} 条记录")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='诊断RIS文件附件问题')
    parser.add_argument('--compare', action='store_true', help='对比单个vs合并RIS')
    parser.add_argument('--extract', action='store_true', help='提取测试样本')

    args = parser.parse_args()

    if args.compare:
        compare_single_vs_merged()
    elif args.extract:
        extract_sample_records()
    else:
        # 默认执行所有诊断
        compare_single_vs_merged()
        extract_sample_records()
