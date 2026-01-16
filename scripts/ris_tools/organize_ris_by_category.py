#!/usr/bin/env python3
"""
替代分类组织方案：将RIS文件按类别复制到不同文件夹，而不是合并
这样可以避免Zotero导入多记录RIS文件时的附件问题
"""

import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Any


def organize_ris_by_category(
    classification: Dict[str, Any],
    records: List[Dict[str, Any]],
    ris_dir: Path,
    output_dir: Path,
    log: logging.Logger
) -> None:
    """
    按类别将单个RIS文件复制到不同文件夹（替代合并方案）

    优点：
    - 保持每个RIS文件独立，避免Zotero多记录导入的附件问题
    - 用户可以直接将整个类别文件夹拖入Zotero
    - 每个文件的附件都能正常显示

    目录结构：
        out_ris_by_category/
        ├── Genomics/
        │   ├── paper1.ris
        │   ├── paper2.ris
        │   └── paper3.ris
        ├── Neuroscience/
        │   ├── paper4.ris
        │   └── paper5.ris
        └── classification_report.json

    Args:
        classification: 分类结果
        records: 记录列表
        ris_dir: 源RIS文件目录
        output_dir: 输出基目录
        log: 日志记录器
    """
    log.info("按类别组织RIS文件（保持单个文件）...")

    # 创建基础目录
    class_base_dir = output_dir / "out_ris_by_category"
    class_base_dir.mkdir(parents=True, exist_ok=True)

    # 创建record_id到record的映射
    record_map = {r["record_id"]: r for r in records}

    # 统计信息
    total_copied = 0
    categories_created = 0

    # 处理每个类别
    categories = classification.get("categories", [])

    for cat in categories:
        cat_name = sanitize_category_name(cat["name"])
        record_ids = cat.get("record_ids", [])

        if not record_ids:
            continue

        # 为每个类别创建子目录
        cat_dir = class_base_dir / cat_name
        cat_dir.mkdir(parents=True, exist_ok=True)
        categories_created += 1

        log.info(f"类别 '{cat_name}': 复制 {len(record_ids)} 个文件")

        # 复制该类别的所有RIS文件
        copied_count = 0
        for record_id in record_ids:
            record = record_map.get(record_id)
            if not record:
                continue

            ris_filename = record["ris_filename"]
            src_path = ris_dir / ris_filename
            dst_path = cat_dir / ris_filename

            if src_path.exists():
                try:
                    shutil.copy2(src_path, dst_path)
                    copied_count += 1
                    total_copied += 1
                except Exception as e:
                    log.warning(f"无法复制 {ris_filename}: {e}")
            else:
                log.warning(f"RIS文件不存在: {src_path}")

        log.info(f"  -> 创建目录 {cat_dir.name}/ 包含 {copied_count} 个文件")

    # 处理未分类文档
    uncategorized = classification.get("uncategorized", [])
    if uncategorized:
        cat_dir = class_base_dir / "Uncategorized"
        cat_dir.mkdir(parents=True, exist_ok=True)
        categories_created += 1

        log.info(f"类别 'Uncategorized': 复制 {len(uncategorized)} 个文件")

        copied_count = 0
        for record_id in uncategorized:
            record = record_map.get(record_id)
            if not record:
                continue

            ris_filename = record["ris_filename"]
            src_path = ris_dir / ris_filename
            dst_path = cat_dir / ris_filename

            if src_path.exists():
                try:
                    shutil.copy2(src_path, dst_path)
                    copied_count += 1
                    total_copied += 1
                except Exception as e:
                    log.warning(f"无法复制 {ris_filename}: {e}")

        log.info(f"  -> 创建目录 {cat_dir.name}/ 包含 {copied_count} 个文件")

    log.info(f"分类组织完成: {total_copied} 个文件复制到 {categories_created} 个类别文件夹")

    # 保存分类报告
    report_path = class_base_dir / "classification_report.json"
    report = {
        "total_files": total_copied,
        "total_categories": categories_created,
        "categories": [
            {
                "name": cat["name"],
                "count": len(cat.get("record_ids", []))
            }
            for cat in categories
        ]
    }
    if uncategorized:
        report["categories"].append({
            "name": "Uncategorized",
            "count": len(uncategorized)
        })

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    log.info(f"分类报告已保存: {report_path}")
    log.info(f"\n使用方法: 直接将类别文件夹拖入Zotero，每个RIS文件的附件都会正常显示")


def sanitize_category_name(name: str) -> str:
    """清理类别名称，使其适合作为文件夹名"""
    # 替换不安全字符
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        name = name.replace(char, '_')
    # 移除首尾空格
    name = name.strip()
    # 限制长度
    if len(name) > 50:
        name = name[:50]
    return name


if __name__ == '__main__':
    """独立运行此脚本来重新组织现有的分类结果"""
    import argparse

    parser = argparse.ArgumentParser(
        description='按类别组织RIS文件（保持单个文件，解决Zotero附件问题）'
    )
    parser.add_argument('--classification', type=str,
                       default='outputs2/out_ris_class/classification_report.json',
                       help='分类报告JSON文件')
    parser.add_argument('--ris-dir', type=str,
                       default='outputs2/out_ris',
                       help='源RIS文件目录')
    parser.add_argument('--output-dir', type=str,
                       default='outputs2',
                       help='输出基目录')

    args = parser.parse_args()

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(message)s'
    )
    log = logging.getLogger(__name__)

    # 读取分类报告
    classification_path = Path(args.classification)
    if not classification_path.exists():
        log.error(f"分类报告不存在: {classification_path}")
        exit(1)

    with open(classification_path, 'r', encoding='utf-8') as f:
        report = json.load(f)

    # 重建分类结构（从报告中）
    # 注意：这需要原始的分类数据，而不仅仅是报告
    # 如果报告中没有record_ids，需要从其他地方获取

    log.info("此脚本需要与主程序集成使用")
    log.info("或者手动提供完整的分类数据（包含record_ids）")
