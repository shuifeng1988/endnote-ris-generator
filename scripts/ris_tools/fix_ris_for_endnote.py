#!/usr/bin/env python3
"""
RIS 附件路径修复工具 - 为 EndNote 准备可用的 RIS 文件
修复附件路径，确保 EndNote 能够识别并复制附件到库中
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
import argparse


class RISAttachmentFixer:
    """RIS 附件路径修复器"""

    def __init__(self, output_dir: str = "endnote_ready"):
        """
        初始化修复器

        Args:
            output_dir: 输出目录，用于存放修复后的 RIS 和附件
        """
        self.output_dir = Path(output_dir)
        self.attachments_dir = self.output_dir / "PDF"
        self.output_dir.mkdir(exist_ok=True)
        self.attachments_dir.mkdir(exist_ok=True)

        self.stats = {
            'total_entries': 0,
            'entries_with_attachments': 0,
            'attachments_found': 0,
            'attachments_copied': 0,
            'attachments_missing': 0
        }

    def fix_ris_file(self, input_ris: str, output_ris: str = "fixed_library.ris",
                     pdf_search_dirs: List[str] = None) -> str:
        """
        修复 RIS 文件中的附件路径

        Args:
            input_ris: 输入的 RIS 文件路径
            output_ris: 输出的 RIS 文件名
            pdf_search_dirs: PDF 文件搜索目录列表

        Returns:
            输出的 RIS 文件路径
        """
        if pdf_search_dirs is None:
            pdf_search_dirs = ['.']

        print(f"读取 RIS 文件: {input_ris}")
        entries = self._parse_ris(input_ris)
        print(f"找到 {len(entries)} 个条目")

        self.stats['total_entries'] = len(entries)

        # 构建 PDF 文件索引
        print("\n构建 PDF 文件索引...")
        pdf_index = self._build_pdf_index(pdf_search_dirs)
        print(f"找到 {len(pdf_index)} 个 PDF 文件")

        # 处理每个条目
        print("\n处理条目...")
        fixed_entries = []
        for i, entry in enumerate(entries, 1):
            print(f"\r处理进度: {i}/{len(entries)}", end='', flush=True)
            fixed_entry = self._fix_entry_attachments(entry, pdf_index)
            fixed_entries.append(fixed_entry)

        print()  # 换行

        # 写入修复后的 RIS 文件
        output_path = self.output_dir / output_ris
        self._write_ris(fixed_entries, output_path)

        # 打印统计信息
        self._print_stats()

        return str(output_path)

    def _parse_ris(self, ris_file: str) -> List[Dict[str, List[str]]]:
        """
        解析 RIS 文件

        Args:
            ris_file: RIS 文件路径

        Returns:
            条目列表，每个条目是一个字典
        """
        entries = []
        current_entry = {}

        with open(ris_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.rstrip('\n\r')

                # 空行跳过
                if not line.strip():
                    continue

                # 检查是否是 RIS 标签行
                match = re.match(r'^([A-Z][A-Z0-9])  - (.*)$', line)
                if match:
                    tag, value = match.groups()

                    if tag == 'TY':
                        # 新条目开始
                        if current_entry:
                            entries.append(current_entry)
                        current_entry = {}

                    if tag not in current_entry:
                        current_entry[tag] = []
                    current_entry[tag].append(value)

                elif line.startswith('ER  -'):
                    # 条目结束
                    if current_entry:
                        entries.append(current_entry)
                        current_entry = {}

        # 添加最后一个条目
        if current_entry:
            entries.append(current_entry)

        return entries

    def _build_pdf_index(self, search_dirs: List[str]) -> Dict[str, str]:
        """
        构建 PDF 文件索引

        Args:
            search_dirs: 搜索目录列表

        Returns:
            文件名到完整路径的映射
        """
        pdf_index = {}

        for search_dir in search_dirs:
            search_path = Path(search_dir)
            if not search_path.exists():
                print(f"警告: 目录不存在: {search_dir}")
                continue

            # 递归查找所有 PDF 文件
            for pdf_file in search_path.rglob('*.pdf'):
                # 使用文件名（不含路径）作为键
                filename = pdf_file.name
                # 如果有重复，保留第一个找到的
                if filename not in pdf_index:
                    pdf_index[filename] = str(pdf_file.absolute())

        return pdf_index

    def _fix_entry_attachments(self, entry: Dict[str, List[str]],
                                pdf_index: Dict[str, str]) -> Dict[str, List[str]]:
        """
        修复单个条目的附件路径

        Args:
            entry: RIS 条目
            pdf_index: PDF 文件索引

        Returns:
            修复后的条目
        """
        # 移除所有现有的附件字段
        attachment_tags = ['L1', 'L2', 'L4', 'file']
        for tag in attachment_tags:
            if tag in entry:
                del entry[tag]

        # 查找可能的 PDF 文件
        pdf_files = self._find_pdfs_for_entry(entry, pdf_index)

        if pdf_files:
            self.stats['entries_with_attachments'] += 1
            self.stats['attachments_found'] += len(pdf_files)

            # 复制 PDF 文件并添加路径到条目
            entry['L1'] = []
            for pdf_path in pdf_files:
                copied_path = self._copy_pdf(pdf_path, entry)
                if copied_path:
                    # EndNote 需要相对路径或绝对路径
                    # 这里使用相对路径（相对于 RIS 文件）
                    rel_path = os.path.join('PDF', Path(copied_path).name)
                    entry['L1'].append(rel_path)
                    self.stats['attachments_copied'] += 1

        return entry

    def _find_pdfs_for_entry(self, entry: Dict[str, List[str]],
                             pdf_index: Dict[str, str]) -> List[str]:
        """
        为条目查找匹配的 PDF 文件

        Args:
            entry: RIS 条目
            pdf_index: PDF 文件索引

        Returns:
            匹配的 PDF 文件路径列表
        """
        found_pdfs = []

        # 提取条目信息用于匹配
        title = ' '.join(entry.get('TI', [''])).lower()
        authors = [a.split(',')[0].lower() for a in entry.get('AU', [])]
        year = ''
        for date_field in ['PY', 'DA', 'Y1']:
            if date_field in entry:
                year_match = re.search(r'\d{4}', entry[date_field][0])
                if year_match:
                    year = year_match.group()
                    break

        # 检查现有的附件字段
        for tag in ['L1', 'L2', 'L4', 'file']:
            if tag in entry:
                for path in entry[tag]:
                    # 提取文件名
                    filename = Path(path).name
                    if filename.endswith('.pdf'):
                        # 在索引中查找
                        if filename in pdf_index:
                            found_pdfs.append(pdf_index[filename])
                        else:
                            # 尝试直接使用路径
                            if os.path.exists(path):
                                found_pdfs.append(path)

        # 如果没有找到，尝试基于标题和作者匹配
        if not found_pdfs and title:
            # 生成可能的文件名模式
            title_words = re.findall(r'\w+', title)[:5]  # 取前5个单词
            patterns = []

            if authors and year:
                first_author = authors[0]
                patterns.append(f"{first_author}.*{year}.*\\.pdf")
                patterns.append(f"{first_author}_{year}.*\\.pdf")

            if title_words:
                title_pattern = '.*'.join(title_words[:3])
                patterns.append(f".*{title_pattern}.*\\.pdf")

            # 在索引中搜索匹配的文件
            for filename, filepath in pdf_index.items():
                filename_lower = filename.lower()
                for pattern in patterns:
                    if re.search(pattern, filename_lower):
                        found_pdfs.append(filepath)
                        break

        return found_pdfs

    def _copy_pdf(self, source_path: str, entry: Dict[str, List[str]]) -> str:
        """
        复制 PDF 文件到输出目录

        Args:
            source_path: 源文件路径
            entry: RIS 条目（用于生成文件名）

        Returns:
            目标文件路径，失败返回 None
        """
        try:
            source = Path(source_path)
            if not source.exists():
                self.stats['attachments_missing'] += 1
                return None

            # 生成目标文件名
            dest_filename = self._generate_pdf_filename(entry, source.suffix)
            dest_path = self.attachments_dir / dest_filename

            # 如果文件已存在，添加数字后缀
            counter = 1
            while dest_path.exists():
                name_without_ext = dest_filename.rsplit('.', 1)[0]
                dest_path = self.attachments_dir / f"{name_without_ext}_{counter}.pdf"
                counter += 1

            # 复制文件
            shutil.copy2(source, dest_path)
            return str(dest_path)

        except Exception as e:
            print(f"\n警告: 复制文件失败 {source_path}: {e}")
            self.stats['attachments_missing'] += 1
            return None

    def _generate_pdf_filename(self, entry: Dict[str, List[str]], extension: str = '.pdf') -> str:
        """
        为 PDF 生成文件名

        Args:
            entry: RIS 条目
            extension: 文件扩展名

        Returns:
            文件名
        """
        # 提取作者
        authors = entry.get('AU', [])
        first_author = ''
        if authors:
            first_author = authors[0].split(',')[0]

        # 提取年份
        year = ''
        for date_field in ['PY', 'DA', 'Y1']:
            if date_field in entry:
                year_match = re.search(r'\d{4}', entry[date_field][0])
                if year_match:
                    year = year_match.group()
                    break

        # 提取标题
        title = ' '.join(entry.get('TI', ['untitled']))[:50]

        # 组合文件名
        parts = [p for p in [first_author, year, title] if p]
        filename = '_'.join(parts)

        # 清理非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)

        return f"{filename}{extension}"

    def _write_ris(self, entries: List[Dict[str, List[str]]], output_path: Path):
        """
        写入 RIS 文件

        Args:
            entries: 条目列表
            output_path: 输出文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in entries:
                # 写入类型
                if 'TY' in entry:
                    f.write(f"TY  - {entry['TY'][0]}\n")

                # 写入其他字段
                for tag, values in entry.items():
                    if tag == 'TY':
                        continue
                    for value in values:
                        f.write(f"{tag}  - {value}\n")

                # 写入结束标记
                f.write("ER  -\n\n")

        print(f"\n✓ 修复后的 RIS 文件已保存: {output_path}")

    def _print_stats(self):
        """打印统计信息"""
        print("\n" + "=" * 60)
        print("处理统计")
        print("=" * 60)
        print(f"总条目数: {self.stats['total_entries']}")
        print(f"有附件的条目: {self.stats['entries_with_attachments']}")
        print(f"找到的附件: {self.stats['attachments_found']}")
        print(f"成功复制的附件: {self.stats['attachments_copied']}")
        print(f"缺失的附件: {self.stats['attachments_missing']}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='修复 RIS 文件的附件路径，使其能被 EndNote 正确导入'
    )
    parser.add_argument(
        'input_ris',
        help='输入的 RIS 文件路径'
    )
    parser.add_argument(
        '-o', '--output',
        default='fixed_library.ris',
        help='输出的 RIS 文件名（默认: fixed_library.ris）'
    )
    parser.add_argument(
        '-d', '--output-dir',
        default='endnote_ready',
        help='输出目录（默认: endnote_ready）'
    )
    parser.add_argument(
        '-p', '--pdf-dirs',
        nargs='+',
        default=['.'],
        help='PDF 文件搜索目录（可指定多个，默认: 当前目录）'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("RIS 附件路径修复工具")
    print("=" * 60)
    print()

    fixer = RISAttachmentFixer(output_dir=args.output_dir)

    try:
        output_ris = fixer.fix_ris_file(
            args.input_ris,
            args.output,
            args.pdf_dirs
        )

        print("\n" + "=" * 60)
        print("修复完成！")
        print("=" * 60)
        print(f"\n下一步操作：")
        print(f"1. 将整个 '{args.output_dir}' 文件夹复制到 Windows 系统")
        print(f"2. 在 EndNote 中：")
        print(f"   - File → Import → File")
        print(f"   - 选择 {args.output}")
        print(f"   - Import Option: RefMan (RIS)")
        print(f"   - Duplicates: Import All")
        print(f"   - 在 'Import Options' 中确保选择了 'Copy files to library folder'")
        print(f"3. EndNote 会自动识别 PDF 文件夹中的附件并复制到库中")
        print(f"\n提示：")
        print(f"- 确保 RIS 文件和 PDF 文件夹在同一目录下")
        print(f"- EndNote 会根据 L1 字段中的相对路径查找附件")

    except Exception as e:
        print(f"\n✗ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
