#!/usr/bin/env python3
"""
修复合并RIS文件 - 确保正确的记录分隔和附件字段格式
"""

import sys
from pathlib import Path


def validate_and_fix_ris(input_path, output_path=None):
    """
    验证并修复RIS文件格式

    主要修复：
    1. 确保记录之间有且仅有一个空行
    2. 移除空记录
    3. 保持L1附件字段不变
    4. 确保每条记录以ER  -结尾
    """
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.parent / f"{input_path.stem}_fixed{input_path.suffix}"
    else:
        output_path = Path(output_path)

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按ER  -分割记录
    parts = content.split('ER  -')

    valid_records = []
    for part in parts:
        # 清理每个部分
        part = part.strip()
        if not part:
            continue

        # 检查是否是有效记录（至少包含TY和TI字段）
        if 'TY  -' in part and ('TI  -' in part or 'AU  -' in part):
            # 确保记录以TY开头
            lines = part.split('\n')
            # 移除开头的空行
            while lines and not lines[0].strip():
                lines.pop(0)

            # 确保第一行是TY
            if lines and not lines[0].startswith('TY  -'):
                # 查找TY行
                ty_index = -1
                for i, line in enumerate(lines):
                    if line.startswith('TY  -'):
                        ty_index = i
                        break
                if ty_index > 0:
                    lines = lines[ty_index:]

            if lines:
                valid_records.append('\n'.join(lines))

    if not valid_records:
        print(f"警告: 未找到有效记录")
        return None

    # 重新组合：每条记录后加ER  -，记录之间用空行分隔
    output_lines = []
    for i, record in enumerate(valid_records):
        output_lines.append(record)
        output_lines.append('ER  -')
        # 在记录之间添加空行（最后一条记录除外）
        if i < len(valid_records) - 1:
            output_lines.append('')

    output_content = '\n'.join(output_lines)

    # 确保文件以换行符结尾
    if not output_content.endswith('\n'):
        output_content += '\n'

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_content)

    print(f"✓ 修复完成: {output_path.name}")
    print(f"  有效记录数: {len(valid_records)}")

    return output_path


def check_ris_format(file_path):
    """检查RIS文件格式"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    records = content.split('ER  -')
    valid_count = 0
    empty_count = 0

    print(f"\n文件: {Path(file_path).name}")
    print("-" * 60)

    for i, record in enumerate(records):
        record = record.strip()
        if not record:
            empty_count += 1
            continue

        has_ty = 'TY  -' in record
        has_ti = 'TI  -' in record
        has_l1 = 'L1  -' in record

        if has_ty and has_ti:
            valid_count += 1
            if i < 3:  # 只显示前3条
                print(f"记录 {i+1}:")
                print(f"  TY: {'✓' if has_ty else '✗'}")
                print(f"  TI: {'✓' if has_ti else '✗'}")
                print(f"  L1: {'✓' if has_l1 else '✗'}")
        else:
            print(f"记录 {i+1}: 无效或空记录")
            if i < 5:  # 显示前几条空记录的内容
                print(f"  内容: {record[:100]}...")

    print(f"\n总计:")
    print(f"  有效记录: {valid_count}")
    print(f"  空记录: {empty_count}")
    print(f"  总部分: {len(records)}")


def batch_fix_ris_files(directory):
    """批量修复目录中的RIS文件"""
    directory = Path(directory)
    if not directory.exists():
        print(f"错误: 目录不存在: {directory}")
        return

    ris_files = list(directory.glob("*.ris"))
    # 过滤掉已修复的文件
    ris_files = [f for f in ris_files if '_fixed' not in f.stem]

    if not ris_files:
        print(f"警告: 未找到RIS文件")
        return

    print(f"\n找到 {len(ris_files)} 个RIS文件\n")

    for ris_file in ris_files:
        try:
            validate_and_fix_ris(ris_file)
        except Exception as e:
            print(f"✗ 错误处理 {ris_file.name}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='修复合并RIS文件的格式问题',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 检查文件格式
  python fix_merged_ris_v2.py --check Multi-Omics.ris

  # 修复单个文件
  python fix_merged_ris_v2.py -f Multi-Omics.ris

  # 批量修复目录
  python fix_merged_ris_v2.py -d outputs2/out_ris_class

  # 修复并指定输出
  python fix_merged_ris_v2.py -f input.ris -o output.ris
        """
    )

    parser.add_argument('-f', '--file', type=str, help='要修复的RIS文件')
    parser.add_argument('-o', '--output', type=str, help='输出文件路径（可选）')
    parser.add_argument('-d', '--directory', type=str, help='批量修复目录')
    parser.add_argument('--check', type=str, help='检查RIS文件格式（不修复）')

    args = parser.parse_args()

    if args.check:
        check_ris_format(args.check)
    elif args.file:
        validate_and_fix_ris(args.file, args.output)
    elif args.directory:
        batch_fix_ris_files(args.directory)
    else:
        parser.print_help()
        print("\n错误: 必须指定参数")
        sys.exit(1)
