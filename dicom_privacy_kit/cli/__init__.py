"""CLI interface for DICOM Privacy Kit."""

import argparse
import sys
import logging
from . import anonymize, score, diff

# Configure logging for CLI
logging.basicConfig(
    format='%(levelname)s: %(message)s',
    level=logging.WARNING
)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='dicom-privacy-kit',
        description='Tools for anonymizing and assessing DICOM files'
    )
    
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Register subcommands
    anonymize.setup_parser(subparsers)
    score.setup_parser(subparsers)
    diff.setup_parser(subparsers)
    
    # Parse and execute
    args = parser.parse_args()
    
    # Set logging level if debug is requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if hasattr(args, 'func'):
        try:
            exit_code = args.func(args)
            sys.exit(exit_code if exit_code is not None else 0)
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
            if args.debug:
                import traceback
                traceback.print_exc(file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == '__main__':
    main()
