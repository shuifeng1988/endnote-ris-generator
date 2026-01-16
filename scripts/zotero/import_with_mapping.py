#!/usr/bin/env python3
"""
改进的Zotero导入脚本
- 在导入时建立ref_id映射
- 保存 ref_id -> zotero_item_key -> pdf_path
- 支持后续精确的PDF上传
"""

import os
import json
import re
from pathlib import Path
from urllib.parse import unquote
from typing import Dict, List, Any

# 修复代理问题
if 'ALL_PROXY' in os.environ and 'socks' in os.environ['ALL_PROXY'].lower():
    print("检测到socks代理，临时禁用（pyzotero不支持socks）...")
    del os.environ['ALL_PROXY']
if 'all_proxy' in os.environ and 'socks' in os.environ['all_proxy'].lower():
    del os.environ['all_proxy']

try:
    from pyzotero import zotero
except ImportError:
    print("错误: 需要安装 pyzotero")
    exit(1)


class ZoteroImporterWithMapping:
    """带ID映射的Zotero导入器"""

    def __init__(self, library_id, api_key, library_type='user'):
        self.zot = zotero.Zotero(library_id, library_type, api_key)
        print(f"✓ 已连接到Zotero (Library ID: {library_id})")

        # 存储映射: ref_id -> {item_key, pdf_path, title, collection}
        self.mapping = {}

    def parse_ris_file(self, ris_path):
        """解析RIS文件，提取所有记录和ref_id"""
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
        """解析单条RIS记录，提取ref_id和PDF路径"""
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
            'ref_id': None,  # EndNote folder名称
            'pdf_path': None
        }

        lines = ris_text.split('\n')
        current_field = None
        current_value = []

        for line in lines:
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
            # 提取ref_id (EndNote folder名称)
            folder_match = re.search(r'EndNote folder=([^|]+)', value)
            if folder_match:
                record['ref_id'] = folder_match.group(1).strip()

            # 提取PDF路径
            attach_match = re.search(r'attachments=(file://[^\s\|]+)', value)
            if attach_match:
                pdf_url = attach_match.group(1)
                if pdf_url.startswith('file:///'):
                    pdf_path = pdf_url[7:]
                elif pdf_url.startswith('file://'):
                    pdf_path = pdf_url[7:]
                else:
                    pdf_path = pdf_url
                record['pdf_path'] = unquote(pdf_path)

    def create_collection(self, collection_name, parent_collection=None):
        """创建集合"""
        try:
            collections = self.zot.collections()
            for col in collections:
                if col['data']['name'] == collection_name:
                    print(f"  集合已存在: {collection_name}")
                    return col['key']

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

    def import_item_and_record_mapping(self, item_data, ref_id, pdf_path, collection_key, collection_name):
        """导入条目并记录映射"""
        try:
            # 移除内部字段
            for field in ['pdf_path', 'ref_id']:
                if field in item_data:
                    del item_data[field]

            # 创建条目
            if collection_key:
                item_data['collections'] = [collection_key]

            result = self.zot.create_items([item_data])

            if 'successful' not in result or not result['successful']:
                error_msg = "未知错误"
                if 'failed' in result and result['failed']:
                    for key, error in result['failed'].items():
                        error_msg = str(error)
                        break
                print(f"  ✗ 创建条目失败: {item_data.get('title', 'Unknown')[:50]}")
                print(f"     错误: {error_msg}")
                return False

            item_key = result['successful']['0']['key']

            # 保存映射
            self.mapping[ref_id] = {
                'item_key': item_key,
                'pdf_path': pdf_path,
                'title': item_data.get('title', ''),
                'collection': collection_name
            }

            # 输出
            if pdf_path and Path(pdf_path).exists():
                print(f"  ✓ {item_data['title'][:60]}... [PDF: {Path(pdf_path).name[:30]}]")
            else:
                print(f"  ✓ {item_data['title'][:60]}... [No PDF]")

            return True

        except Exception as e:
            print(f"  ✗ 导入失败: {str(e)[:100]}")
            return False

    def import_category(self, category_name, ris_path):
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

        for i, record in enumerate(records, 1):
            ref_id = record.get('ref_id') or f"{category_name}_{i}"
            pdf_path = record.get('pdf_path')

            if self.import_item_and_record_mapping(
                record, ref_id, pdf_path, collection_key, category_name
            ):
                success_count += 1
                if pdf_path and Path(pdf_path).exists():
                    pdf_count += 1

        print(f"\n总结:")
        print(f"  成功导入: {success_count}/{len(records)}")
        print(f"  有PDF路径: {pdf_count}/{len(records)}")

    def import_all_categories(self, ris_dir):
        """批量导入所有类别"""
        ris_dir = Path(ris_dir)
        ris_files = list(ris_dir.glob("*.ris"))

        print(f"\n{'='*70}")
        print(f"全自动导入开始")
        print(f"{'='*70}")
        print(f"RIS目录: {ris_dir}")
        print(f"类别数: {len(ris_files)}")
        print(f"{'='*70}\n")

        for ris_file in sorted(ris_files):
            if ris_file.stem == 'classification_report':
                continue

            category_name = ris_file.stem
            self.import_category(category_name, ris_file)

        print(f"\n{'='*70}")
        print(f"全部导入完成！")
        print(f"{'='*70}")

    def save_mapping(self, output_file='zotero_item_mapping.json'):
        """保存映射到JSON文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.mapping, f, indent=2, ensure_ascii=False)
        print(f"\n✓ 映射已保存到: {output_file}")
        print(f"  总条目数: {len(self.mapping)}")
        pdf_count = sum(1 for v in self.mapping.values() if v['pdf_path'] and Path(v['pdf_path']).exists())
        print(f"  有PDF: {pdf_count}/{len(self.mapping)}")


def load_config():
    """加载Zotero配置"""
    config_file = Path('.zotero_config.json')
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config['library_id'], config['api_key'], config.get('library_type', 'user')
    else:
        print("错误: 找不到配置文件")
        exit(1)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='改进的Zotero导入（带ID映射）',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--ris-dir',
        default='outputs2/out_ris_class',
        help='RIS文件目录'
    )
    parser.add_argument(
        '--category',
        help='只导入指定类别'
    )
    parser.add_argument(
        '--mapping-file',
        default='zotero_item_mapping.json',
        help='映射文件输出路径'
    )

    args = parser.parse_args()

    # 加载配置
    library_id, api_key, library_type = load_config()

    # 创建导入器
    try:
        importer = ZoteroImporterWithMapping(library_id, api_key, library_type)
    except Exception as e:
        print(f"\n错误: 无法连接到Zotero API")
        print(f"详情: {e}")
        exit(1)

    # 执行导入
    if args.category:
        ris_file = Path(args.ris_dir) / f"{args.category}.ris"
        if not ris_file.exists():
            print(f"错误: 文件不存在: {ris_file}")
            exit(1)
        importer.import_category(args.category, ris_file)
    else:
        importer.import_all_categories(args.ris_dir)

    # 保存映射
    importer.save_mapping(args.mapping_file)

    print("\n完成！")
