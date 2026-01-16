#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zotero Tools - Unified CLI Entry Point

Main commands:
  attach      Attach PDFs to Zotero items (3 methods available)
  import      Import items to Zotero with various strategies
  clean       Clean and organize Zotero library
  check       Check collections and library status
  restore     Restore Zotero library from EndNote PDF directories

Usage:
  python zotero_cli.py attach [--method smart|ris|basic] [options]
  python zotero_cli.py import [--method auto|mapping] [options]
  python zotero_cli.py clean [--unfiled|--full] [options]
  python zotero_cli.py check [options]
  python zotero_cli.py restore [options]

For detailed help on each command:
  python zotero_cli.py attach --help
  python zotero_cli.py import --help
"""

import sys
import argparse
from pathlib import Path

# Add scripts directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR / "scripts" / "zotero"))


def main():
    parser = argparse.ArgumentParser(
        description="Zotero Tools - Unified CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Attach command
    attach_parser = subparsers.add_parser(
        'attach',
        help='Attach PDFs to Zotero items'
    )
    attach_parser.add_argument(
        '--method',
        choices=['smart', 'ris', 'basic'],
        default='smart',
        help='Attachment method: smart (intelligent matching), ris (from RIS file), basic (simple upload)'
    )

    # Import command
    import_parser = subparsers.add_parser(
        'import',
        help='Import items to Zotero'
    )
    import_parser.add_argument(
        '--method',
        choices=['auto', 'mapping'],
        default='auto',
        help='Import method: auto (automatic), mapping (with item mapping)'
    )

    # Clean command
    clean_parser = subparsers.add_parser(
        'clean',
        help='Clean and organize Zotero library'
    )
    clean_parser.add_argument(
        '--unfiled',
        action='store_true',
        help='Only clean unfiled items'
    )
    clean_parser.add_argument(
        '--full',
        action='store_true',
        help='Full library cleanup'
    )

    # Check command
    check_parser = subparsers.add_parser(
        'check',
        help='Check collections and library status'
    )

    # Restore command
    restore_parser = subparsers.add_parser(
        'restore',
        help='Restore Zotero library from EndNote PDF directories'
    )

    # Parse known args to allow passing through to subscripts
    args, remaining = parser.parse_known_args()

    if not args.command:
        parser.print_help()
        return 0

    # Route to appropriate script
    if args.command == 'attach':
        if args.method == 'smart':
            from smart_attach_pdfs import main as attach_main
        elif args.method == 'ris':
            from attach_with_ris import main as attach_main
        else:
            from attach_pdfs import main as attach_main

        sys.argv = [sys.argv[0]] + remaining
        return attach_main()

    elif args.command == 'import':
        if args.method == 'auto':
            from auto_import_zotero import main as import_main
        else:
            from import_with_mapping import main as import_main

        sys.argv = [sys.argv[0]] + remaining
        return import_main()

    elif args.command == 'clean':
        if args.unfiled:
            from clean_unfiled_items import main as clean_main
        else:
            from clean_zotero import main as clean_main

        sys.argv = [sys.argv[0]] + remaining
        return clean_main()

    elif args.command == 'check':
        from check_collections import main as check_main
        sys.argv = [sys.argv[0]] + remaining
        return check_main()

    elif args.command == 'restore':
        from zotero_restore_from_endnote_pdf_directories import main as restore_main
        sys.argv = [sys.argv[0]] + remaining
        return restore_main()

    return 0


if __name__ == "__main__":
    sys.exit(main())
