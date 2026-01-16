#!/usr/bin/env python3
"""
生成无附件的纯元数据RIS文件
配合Zotero的自动附件功能使用
"""

from pathlib import Path
import shutil


def create_metadata_only_ris(input_dir, output_dir):
    """
    创建只包含元数据（无L1附件字段）的RIS文件

    Zotero会根据DOI等信息自动下载或关联附件
    """
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 创建分类子目录映射
    category_dirs = {}

    print("处理RIS文件，移除本地附件路径...")

    # 遍历分类目录
    for cat_dir in input_dir.iterdir():
        if not cat_dir.is_dir():
            continue

        cat_name = cat_dir.name
        out_cat_dir = output_dir / cat_name
        out_cat_dir.mkdir(parents=True, exist_ok=True)
        category_dirs[cat_name] = out_cat_dir

        # 处理该类别下的所有RIS文件
        processed = 0
        for ris_file in cat_dir.glob("*.ris"):
            with open(ris_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 移除L1和N1中的附件信息
            clean_lines = []
            for line in lines:
                # 跳过L1字段（本地文件链接）
                if line.startswith('L1  - '):
                    continue
                # 保留N1但可选择性清理
                # if line.startswith('N1  - '):
                #     continue
                clean_lines.append(line)

            # 写入新文件
            out_file = out_cat_dir / ris_file.name
            with open(out_file, 'w', encoding='utf-8') as f:
                f.writelines(clean_lines)

            processed += 1

        print(f"✓ {cat_name}: 处理了 {processed} 个文件")

    print(f"\n完成！输出目录: {output_dir}")
    print("\n下一步：")
    print("1. 在Zotero中导入这些纯元数据RIS文件")
    print("2. 使用Zotfile插件或手动关联PDF文件")


def create_pdf_to_metadata_mapping(ris_dir, pdf_dir, output_file):
    """
    创建PDF文件名到元数据的映射，用于后续批量关联
    """
    ris_dir = Path(ris_dir)
    pdf_dir = Path(pdf_dir)

    mapping = {}

    for ris_file in ris_dir.glob("**/*.ris"):
        with open(ris_file, 'r', encoding='utf-8') as f:
            content = f.read()

        title = None
        doi = None
        pdf_path = None

        for line in content.split('\n'):
            if line.startswith('TI  - '):
                title = line[6:].strip()
            elif line.startswith('DO  - '):
                doi = line[6:].strip()
            elif line.startswith('L1  - '):
                pdf_path = line[6:].strip()

        if pdf_path and title:
            # 从file:///路径提取文件名
            pdf_name = pdf_path.split('/')[-1]
            pdf_name = pdf_name.replace('%20', ' ')
            mapping[pdf_name] = {
                'title': title,
                'doi': doi,
                'original_path': pdf_path
            }

    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    print(f"映射文件已创建: {output_file}")
    print(f"包含 {len(mapping)} 个PDF到元数据的映射")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='创建无附件的纯元数据RIS')
    parser.add_argument('--input', default='outputs2/out_ris_by_category',
                       help='输入RIS目录')
    parser.add_argument('--output', default='outputs2/out_ris_metadata_only',
                       help='输出目录')
    parser.add_argument('--create-mapping', action='store_true',
                       help='创建PDF映射文件')
    parser.add_argument('--pdf-dir', default='/media/shuifeng/BEA6-BBCE/pdfs',
                       help='PDF文件目录')

    args = parser.parse_args()

    if args.create_mapping:
        create_pdf_to_metadata_mapping(
            args.input,
            args.pdf_dir,
            'outputs2/pdf_metadata_mapping.json'
        )
    else:
        create_metadata_only_ris(args.input, args.output)
