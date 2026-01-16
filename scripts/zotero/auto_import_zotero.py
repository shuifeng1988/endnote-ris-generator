#!/usr/bin/env python3
"""
全自动导入脚本 - 使用Zotero API
一次性完成：创建集合 + 导入元数据 + 关联PDF附件
"""

import os
import json
import re
from pathlib import Path
from urllib.parse import unquote
from typing import Dict, List, Any

# 修复代理问题：移除socks代理，pyzotero不支持socks
if 'ALL_PROXY' in os.environ and 'socks' in os.environ['ALL_PROXY'].lower():
    print("检测到socks代理，临时禁用（pyzotero不支持socks）...")
    del os.environ['ALL_PROXY']
if 'all_proxy' in os.environ and 'socks' in os.environ['all_proxy'].lower():
    del os.environ['all_proxy']

try:
    from pyzotero import zotero
except ImportError:
    print("错误: 需要安装 pyzotero")
    print("运行: pip install pyzotero")
    exit(1)


class ZoteroAutoImporter:
    """全自动Zotero导入器"""

    def __init__(self, library_id, api_key, library_type='user'):
        """
        初始化Zotero连接

        Args:
            library_id: Zotero Library ID
            api_key: Zotero API Key
            library_type: 'user' 或 'group'
        """
        self.zot = zotero.Zotero(library_id, library_type, api_key)
        print(f"✓ 已连接到Zotero (Library ID: {library_id})")

    def parse_ris_file(self, ris_path):
        """解析RIS文件，提取所有记录"""
        with open(ris_path, 'r', encoding='utf-8') as f:
            content = f.read()

        records = []
        for part in content.split('ER  -'):
            part = part.strip()
            if not part or 'TY  -' not in part:
                continue

            record = self._parse_single_ris_record(part)
            if record:
                records.append(record)

        return records

    def _parse_single_ris_record(self, ris_text):
        """解析单条RIS记录"""
        record = {
            'itemType': 'journalArticle',
            'title': '',
            'creators': [],
            'abstractNote': '',
            'publicationTitle': '',
            'volume': '',
            'issue': '',
            'pages': '',
            'date': '',
            'DOI': '',
            'url': '',
            'extra': '',
            'pdf_path': None
        }

        lines = ris_text.split('\n')
        current_field = None
        current_value = []

        for line in lines:
            # 检查是否是新字段
            if line and len(line) > 6 and line[2:6] == '  - ':
                # 保存之前的字段
                if current_field and current_value:
                    self._save_field(record, current_field, ' '.join(current_value))

                # 开始新字段
                field_code = line[:2]
                field_value = line[6:].strip()
                current_field = field_code
                current_value = [field_value] if field_value else []
            elif current_field and line.strip():
                # 续行
                current_value.append(line.strip())

        # 保存最后一个字段
        if current_field and current_value:
            self._save_field(record, current_field, ' '.join(current_value))

        return record if record['title'] else None

    def _save_field(self, record, field_code, value):
        """保存字段到记录"""
        if field_code == 'TI':
            record['title'] = value
        elif field_code == 'AU':
            # 解析作者
            authors = [a.strip() for a in value.split(',') if a.strip()]
            for author in authors:
                if ',' in author:
                    parts = author.split(',')
                    record['creators'].append({
                        'creatorType': 'author',
                        'lastName': parts[0].strip(),
                        'firstName': parts[1].strip() if len(parts) > 1 else ''
                    })
                else:
                    # 简单解析
                    parts = author.strip().split()
                    if len(parts) >= 2:
                        record['creators'].append({
                            'creatorType': 'author',
                            'lastName': parts[-1],
                            'firstName': ' '.join(parts[:-1])
                        })
                    else:
                        record['creators'].append({
                            'creatorType': 'author',
                            'lastName': author,
                            'firstName': ''
                        })
        elif field_code == 'PY':
            record['date'] = value
        elif field_code == 'JO' or field_code == 'T2':
            record['publicationTitle'] = value
        elif field_code == 'VL':
            record['volume'] = value
        elif field_code == 'IS':
            record['issue'] = value
        elif field_code == 'SP':
            record['pages'] = value
        elif field_code == 'DO':
            record['DOI'] = value
        elif field_code == 'UR':
            record['url'] = value
        elif field_code == 'N2' or field_code == 'AB':
            record['abstractNote'] = value
        elif field_code == 'N1':
            # 改进的PDF路径提取逻辑
            # 查找 attachments=file:///... 模式
            match = re.search(r'attachments=(file://[^\s\|]+)', value)
            if match:
                pdf_url = match.group(1)
                # 移除 file:// 或 file:/// 前缀
                if pdf_url.startswith('file:///'):
                    pdf_path = pdf_url[7:]  # 移除file://，保留一个/
                elif pdf_url.startswith('file://'):
                    pdf_path = pdf_url[7:]
                else:
                    pdf_path = pdf_url

                # URL解码（处理%20, %E2%80%90等）
                pdf_path = unquote(pdf_path)
                record['pdf_path'] = pdf_path

    def create_collection(self, collection_name, parent_collection=None):
        """创建集合"""
        try:
            # 检查集合是否已存在
            collections = self.zot.collections()
            for col in collections:
                if col['data']['name'] == collection_name:
                    print(f"  集合已存在: {collection_name}")
                    return col['key']

            # 创建新集合
            collection_data = {
                'name': collection_name,
                'parentCollection': parent_collection
            }
            result = self.zot.create_collections([collection_data])
            collection_key = result['successful']['0']['key']
            print(f"  ✓ 创建集合: {collection_name}")
            return collection_key
        except Exception as e:
            print(f"  ✗ 创建集合失败: {e}")
            return None

    def import_item_with_attachment(self, item_data, pdf_path, collection_key=None, debug=False):
        """导入条目并关联PDF"""
        try:
            # 移除内部使用的pdf_path字段（不是Zotero API的有效字段）
            if 'pdf_path' in item_data:
                del item_data['pdf_path']

            # 创建条目
            if collection_key:
                item_data['collections'] = [collection_key]

            if debug:
                print(f"\n  [调试] 准备导入:")
                print(f"    标题: {item_data.get('title', 'N/A')[:80]}")
                print(f"    作者: {len(item_data.get('creators', []))} 个")
                print(f"    DOI: {item_data.get('DOI', 'N/A')}")

            result = self.zot.create_items([item_data])

            if 'successful' not in result or not result['successful']:
                error_msg = "未知错误"
                if 'failed' in result and result['failed']:
                    # 获取详细错误信息
                    for key, error in result['failed'].items():
                        error_msg = str(error)
                        break
                print(f"  ✗ 创建条目失败: {item_data.get('title', 'Unknown')[:50]}")
                print(f"     错误: {error_msg}")
                return False

            item_key = result['successful']['0']['key']

            # 注意：Zotero Web API不支持创建本地链接附件
            # PDF将在导入后通过ZotMoov手动关联
            if pdf_path and Path(pdf_path).exists():
                print(f"  ✓ {item_data['title'][:60]}... [PDF found: {Path(pdf_path).name[:40]}]")
            else:
                print(f"  ✓ {item_data['title'][:60]}... [No PDF]")

            return True

        except Exception as e:
            print(f"  ✗ 导入失败: {str(e)[:100]}")
            return False

    def import_category(self, category_name, ris_path, pdf_dir):
        """导入一个类别的所有文献"""
        print(f"\n{'='*70}")
        print(f"导入类别: {category_name}")
        print(f"{'='*70}")

        # 创建集合
        collection_key = self.create_collection(category_name)
        if not collection_key:
            return

        # 解析RIS文件
        records = self.parse_ris_file(ris_path)
        print(f"  找到 {len(records)} 条记录")

        # 导入每条记录
        success_count = 0
        pdf_count = 0
        pdf_dir = Path(pdf_dir)

        for i, record in enumerate(records, 1):
            # 查找PDF文件
            pdf_path = None

            # 方法1: 从record中提取的pdf_path
            if record.get('pdf_path'):
                extracted_path = record['pdf_path']
                if Path(extracted_path).exists():
                    pdf_path = extracted_path
                else:
                    # 尝试只用文件名在pdf_dir中查找
                    filename = Path(extracted_path).name
                    alternative_path = pdf_dir / filename
                    if alternative_path.exists():
                        pdf_path = str(alternative_path)

            # 方法2: 如果方法1失败，尝试智能匹配
            if not pdf_path:
                pdf_path = self._find_pdf_by_metadata(pdf_dir, record)

            # 导入条目
            if self.import_item_with_attachment(record, pdf_path, collection_key):
                success_count += 1
                if pdf_path and Path(pdf_path).exists():
                    pdf_count += 1

        print(f"\n总结:")
        print(f"  成功导入: {success_count}/{len(records)}")
        print(f"  找到PDF: {pdf_count}/{len(records)}")
        if pdf_count < len(records):
            print(f"  未找到PDF: {len(records) - pdf_count} 条")


    def _find_pdf_by_metadata(self, pdf_dir, record):
        """根据元数据智能查找PDF文件"""
        pdf_dir = Path(pdf_dir)

        # 获取标题，规范化处理
        title = record.get('title', '')
        if not title:
            return None

        # 规范化函数：移除特殊字符，统一空格
        def normalize(text):
            # 统一破折号（全角、半角、特殊Unicode）
            text = text.replace('—', '-').replace('–', '-').replace('‐', '-')
            text = text.replace('\u2010', '-').replace('\u2011', '-').replace('\u2012', '-')
            text = text.replace('\u2013', '-').replace('\u2014', '-').replace('\u2015', '-')
            # 移除标点和特殊字符，保留字母数字空格
            text = re.sub(r'[^\w\s-]', ' ', text, flags=re.UNICODE)
            # 统一多个空格为单个
            text = re.sub(r'\s+', ' ', text)
            return text.strip().lower()

        normalized_title = normalize(title)

        # 策略1: 使用标题前50字符精确匹配
        title_prefix = normalized_title[:50] if len(normalized_title) > 50 else normalized_title

        for pdf in pdf_dir.glob("*.pdf"):
            pdf_name_normalized = normalize(pdf.stem)

            # 完全匹配
            if pdf_name_normalized == normalized_title:
                return str(pdf)

            # 前缀匹配（标题的前50字符）
            if title_prefix in pdf_name_normalized or pdf_name_normalized in title_prefix:
                return str(pdf)

            # 模糊匹配：计算相似度（标题关键词匹配）
            title_words = set(normalized_title.split())
            pdf_words = set(pdf_name_normalized.split())

            # 移除常见停用词
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            title_words -= stop_words
            pdf_words -= stop_words

            if title_words and pdf_words:
                # 计算词汇重叠率
                overlap = len(title_words & pdf_words) / len(title_words)
                if overlap > 0.6:  # 60%以上的词汇匹配
                    return str(pdf)

        # 策略2: 按DOI查找（如果有DOI）
        doi = record.get('DOI', '')
        if doi:
            # 提取DOI的关键部分（去掉前缀）
            doi_part = doi.split('/')[-1].lower() if '/' in doi else doi.lower()
            for pdf in pdf_dir.glob("*.pdf"):
                if doi_part in pdf.name.lower():
                    return str(pdf)

        return None

    def import_all_categories(self, ris_dir, pdf_dir):
        """批量导入所有类别"""
        ris_dir = Path(ris_dir)
        ris_files = list(ris_dir.glob("*.ris"))

        print(f"\n{'='*70}")
        print(f"全自动导入开始")
        print(f"{'='*70}")
        print(f"RIS目录: {ris_dir}")
        print(f"PDF目录: {pdf_dir}")
        print(f"类别数: {len(ris_files)}")
        print(f"{'='*70}\n")

        for ris_file in sorted(ris_files):
            category_name = ris_file.stem
            self.import_category(category_name, ris_file, pdf_dir)

        print(f"\n{'='*70}")
        print(f"全部导入完成！")
        print(f"{'='*70}")
        print(f"\n下一步：使用ZotMoov批量关联PDF")
        print(f"{'='*70}")
        print(f"1. 打开Zotero")
        print(f"2. 配置ZotMoov:")
        print(f"   - Tools → ZotMoov Preferences")
        print(f"   - Source Folder: {pdf_dir}")
        print(f"3. 批量关联PDF:")
        print(f"   - 选中所有导入的条目 (Ctrl+A)")
        print(f"   - 右键 → ZotMoov → Attach from Source Folder")
        print(f"4. 完成！所有PDF将自动关联")
        print(f"{'='*70}\n")


def get_zotero_credentials():
    """获取Zotero API凭证"""
    print("\n" + "="*70)
    print("Zotero API 设置")
    print("="*70)
    print("\n如何获取API凭证:")
    print("1. 访问: https://www.zotero.org/settings/keys")
    print("2. 点击 'Create new private key'")
    print("3. 设置权限:")
    print("   - Personal Library: Read/Write")
    print("   - Default Group Permissions: None")
    print("4. 保存并复制API Key")
    print("\nLibrary ID 获取:")
    print("1. 访问: https://www.zotero.org/settings/keys")
    print("2. 在页面顶部可以看到 'Your userID for use in API calls is XXXXXX'")
    print("="*70 + "\n")

    # 尝试从配置文件读取
    config_file = Path('.zotero_config.json')
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        print(f"✓ 从配置文件读取: {config_file}")
        return config['library_id'], config['api_key'], config.get('library_type', 'user')

    # 手动输入
    library_id = input("请输入 Library ID: ").strip()
    api_key = input("请输入 API Key: ").strip()
    library_type = input("Library类型 (user/group) [user]: ").strip() or 'user'

    # 保存配置
    save = input("\n是否保存配置到 .zotero_config.json? (y/n) [n]: ").strip().lower()
    if save == 'y':
        config = {
            'library_id': library_id,
            'api_key': api_key,
            'library_type': library_type
        }
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✓ 配置已保存到: {config_file}")

    return library_id, api_key, library_type


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='全自动导入到Zotero（使用API）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 首次运行（需要输入API凭证）
  python3 auto_import_zotero.py

  # 使用保存的配置
  python3 auto_import_zotero.py --ris-dir outputs2/out_ris_merged_no_attachment

  # 只导入特定类别
  python3 auto_import_zotero.py --category Multi-Omics

  # 指定PDF目录
  python3 auto_import_zotero.py --pdf-dir /media/shuifeng/BEA6-BBCE/pdfs
        """
    )

    parser.add_argument(
        '--ris-dir',
        default='outputs2/out_ris_merged_no_attachment',
        help='RIS文件目录'
    )
    parser.add_argument(
        '--pdf-dir',
        default='/media/shuifeng/BEA6-BBCE/pdfs',
        help='PDF文件目录'
    )
    parser.add_argument(
        '--category',
        help='只导入指定类别（文件名不含.ris后缀）'
    )
    parser.add_argument(
        '--library-id',
        help='Zotero Library ID（跳过交互式输入）'
    )
    parser.add_argument(
        '--api-key',
        help='Zotero API Key（跳过交互式输入）'
    )

    args = parser.parse_args()

    # 获取API凭证
    if args.library_id and args.api_key:
        library_id = args.library_id
        api_key = args.api_key
        library_type = 'user'
    else:
        library_id, api_key, library_type = get_zotero_credentials()

    # 创建导入器
    try:
        importer = ZoteroAutoImporter(library_id, api_key, library_type)
    except Exception as e:
        print(f"\n错误: 无法连接到Zotero API")
        print(f"详情: {e}")
        print("\n请检查:")
        print("1. Library ID 和 API Key 是否正确")
        print("2. API Key 是否有读写权限")
        print("3. 网络连接是否正常")
        exit(1)

    # 执行导入
    if args.category:
        # 导入单个类别
        ris_file = Path(args.ris_dir) / f"{args.category}.ris"
        if not ris_file.exists():
            print(f"错误: 文件不存在: {ris_file}")
            exit(1)
        importer.import_category(args.category, ris_file, args.pdf_dir)
    else:
        # 导入所有类别
        importer.import_all_categories(args.ris_dir, args.pdf_dir)

    print("\n全自动导入完成！请打开Zotero查看结果。")
