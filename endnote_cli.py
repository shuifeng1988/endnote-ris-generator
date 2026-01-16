#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EndNote Tools - Unified CLI Entry Point

Main commands:
  create      Create EndNote-compatible RIS from directory structure
  export      Export RIS files with custom settings

Usage:
  python endnote_cli.py create [options]
  python endnote_cli.py export [options]

For detailed help on each command:
  python endnote_cli.py create --help
  python endnote_cli.py export --help
"""

import sys
import argparse
from pathlib import Path

# Add scripts directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR / "scripts" / "endnote"))


def main():
    parser = argparse.ArgumentParser(
        description="EndNote Tools - Unified CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create command
    create_parser = subparsers.add_parser(
        'create',
        help='Create EndNote-compatible RIS from directory structure'
    )
    create_parser.add_argument(
        '--script',
        choices=['from_directory', 'ris_from_directory'],
        default='from_directory',
        help='Which creation script to use (default: from_directory)'
    )

    # Export command
    export_parser = subparsers.add_parser(
        'export',
        help='Export RIS files with custom settings'
    )

    # Parse known args to allow passing through to subscripts
    args, remaining = parser.parse_known_args()

    if not args.command:
        parser.print_help()
        return 0

    # Route to appropriate script
    if args.command == 'create':
        if args.script == 'from_directory':
            from create_endnote_from_directory import main as create_main
        else:
            from create_endnote_ris_from_directory import main as create_main

        # Restore sys.argv for the subscript
        sys.argv = [sys.argv[0]] + remaining
        return create_main()

    elif args.command == 'export':
        from endnote_ris_export import main as export_main
        sys.argv = [sys.argv[0]] + remaining
        return export_main()

    return 0


if __name__ == "__main__":
    sys.exit(main())
