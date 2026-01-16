#!/usr/bin/env python3
"""
创建PDF符号链接，使用标准化文件名
提高ZotMoov的自动匹配率
"""

import json
import re
from pathlib import Path
from urllib.parse import unquote


def sanitize_filename(name):
    """清理文件名，移除非法字符"""
    # 移除或替换不安全字符
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    # 移除多余空格
    name = re.sub(r'\s+', ' ', name)
    # 限制长度
    if len(name) > 200:
        name = name[:200]
    return name.strip()


def create_standardized_links(
    ris_dir,
    pdf_dir,
    link_dir,
    format_pattern="{title}"
):
    """
    为PDF创建标准化文件名的符号链接

    Args:
        ris_dir: RIS文件目录
        pdf_dir: 原始PDF目录
        link_dir: 符号链接输出目录
        format_pattern: 文件名格式，可用变量：
            {title}: 标题
            {author}: 第一作者
            {year}: 年份
            {doi}: DOI
    """
    ris_dir = Path(ris_dir)
    pdf_dir = Path(pdf_dir)
    link_dir = Path(link_dir)
    link_dir.mkdir(parents=True, exist_ok=True)

    print(f"处理RIS文件: {ris_dir}")
    print(f"源PDF目录: {pdf_dir}")
    print(f"链接输出: {link_dir}")
    print(f"文件名格式: {format_pattern}\n")

    created = 0
    failed = 0
    skipped = 0

    # 遍历所有RIS文件
    for ris_file in ris_dir.glob("**/*.ris"):
        with open(ris_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取元数据
        metadata = {
            'title': None,
            'author': None,
            'year': None,
            'doi': None,
            'original_pdf': None
        }

        for line in content.split('\n'):
            if line.startswith('TI  - '):
                metadata['title'] = line[6:].strip()
            elif line.startswith('AU  - '):
                if not metadata['author']:
                    # 提取第一作者姓氏
                    author = line[6:].strip()
                    metadata['author'] = author.split(',')[0].split()[-1] if ',' in author else author.split()[0]
            elif line.startswith('PY  - '):
                metadata['year'] = line[6:].strip()
            elif line.startswith('DO  - '):
                metadata['doi'] = line[6:].strip()
            elif line.startswith('N1  - ') and 'attachments=' in line:
                # 从N1字段提取原始PDF路径
                match = re.search(r'attachments=([^\s\|]+)', line)
                if match:
                    pdf_path = match.group(1)
                    # 解析file:///路径
                    if pdf_path.startswith('file:///'):
                        pdf_path = pdf_path[8:]  # 移除file:///
                        pdf_path = unquote(pdf_path)  # URL解码
                        metadata['original_pdf'] = Path(pdf_path).name

        if not metadata['title']:
            skipped += 1
            continue

        # 构建新文件名
        try:
            new_name = format_pattern.format(**metadata)
            new_name = sanitize_filename(new_name)
            new_name += '.pdf'
        except KeyError as e:
            print(f"警告: 格式变量 {e} 不可用，使用标题作为文件名")
            new_name = sanitize_filename(metadata['title']) + '.pdf'

        # 查找原始PDF文件
        if metadata['original_pdf']:
            original_pdf = pdf_dir / metadata['original_pdf']
        else:
            # 尝试通过标题匹配
            possible_pdfs = list(pdf_dir.glob(f"*{metadata['title'][:30]}*.pdf"))
            original_pdf = possible_pdfs[0] if possible_pdfs else None

        if not original_pdf or not original_pdf.exists():
            failed += 1
            print(f"✗ 找不到PDF: {metadata['title'][:50]}...")
            continue

        # 创建符号链接
        link_path = link_dir / new_name

        # 如果链接已存在，跳过或覆盖
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()

        try:
            link_path.symlink_to(original_pdf.resolve())
            created += 1
            if created <= 5:  # 只显示前5个
                print(f"✓ {new_name}")
                print(f"  → {original_pdf.name}")
        except Exception as e:
            failed += 1
            print(f"✗ 创建链接失败: {new_name}: {e}")

    print(f"\n完成:")
    print(f"  成功创建: {created} 个链接")
    print(f"  失败: {failed}")
    print(f"  跳过: {skipped}")
    print(f"\n链接目录: {link_dir}")
    print(f"\n使用方法:")
    print(f"  1. 在ZotMoov中设置Source Folder为: {link_dir}")
    print(f"  2. 使用标准化的文件名提高匹配率")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='为PDF创建标准化文件名的符号链接',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用标题作为文件名
  python3 create_pdf_links.py --format "{title}"

  # 使用 作者_年份_标题 格式
  python3 create_pdf_links.py --format "{author}_{year}_{title}"

  # 指定自定义目录
  python3 create_pdf_links.py \\
    --ris-dir outputs2/out_ris_by_category \\
    --pdf-dir /media/shuifeng/BEA6-BBCE/pdfs \\
    --link-dir /tmp/zotero_pdf_links
        """
    )

    parser.add_argument(
        '--ris-dir',
        default='outputs2/out_ris_by_category',
        help='RIS文件目录'
    )
    parser.add_argument(
        '--pdf-dir',
        default='/media/shuifeng/BEA6-BBCE/pdfs',
        help='原始PDF目录'
    )
    parser.add_argument(
        '--link-dir',
        default='outputs2/pdf_links_standardized',
        help='符号链接输出目录'
    )
    parser.add_argument(
        '--format',
        default='{title}',
        help='文件名格式（可用: title, author, year, doi）'
    )

    args = parser.parse_args()

    create_standardized_links(
        args.ris_dir,
        args.pdf_dir,
        args.link_dir,
        args.format
    )
