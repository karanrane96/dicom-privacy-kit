"""CLI command for comparing DICOM files."""

import argparse
import logging
import sys
from pathlib import Path
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from ..diff import compare_datasets, format_diff

logger = logging.getLogger(__name__)


def diff_command(args):
    """Execute diff command.
    
    Returns:
        0 on success, 1 on failure
    """
    before_path = Path(args.before)
    after_path = Path(args.after)
    
    # Validate input files exist
    if not before_path.exists():
        print(f"ERROR: Before file not found: {before_path}", file=sys.stderr)
        return 1
    if not after_path.exists():
        print(f"ERROR: After file not found: {after_path}", file=sys.stderr)
        return 1
    
    try:
        # Load DICOM files
        print(f"Loading: {before_path}")
        before_dataset = dcmread(str(before_path))
        logger.debug(f"Loaded 'before' DICOM with {len(before_dataset)} elements")
        
        print(f"Loading: {after_path}")
        after_dataset = dcmread(str(after_path))
        logger.debug(f"Loaded 'after' DICOM with {len(after_dataset)} elements")
        
        # Compare
        print("\nComparing datasets...")
        diff = compare_datasets(before_dataset, after_dataset)
        
        # Display summary
        print(f"\nCOMPARISON RESULTS:")
        print(f"  Removed:  {len(diff.removed)} tags")
        print(f"  Added:    {len(diff.added)} tags")
        print(f"  Modified: {len(diff.modified)} tags")
        print(f"  Unchanged: {len(diff.unchanged)} tags")
        
        # Display detailed results
        print(f"\n{format_diff(diff, show_unchanged=args.show_unchanged)}")
        
        # Exit with error if there are significant changes
        if args.fail_on_changes:
            changes = len(diff.removed) + len(diff.added) + len(diff.modified)
            if changes > 0:
                print(f"\nERROR: Found {changes} changes", file=sys.stderr)
                return 1
        
        print(f"\nSUCCESS: Comparison complete")
        return 0
        
    except InvalidDicomError as e:
        print(f"ERROR: Invalid DICOM file: {e}", file=sys.stderr)
        logger.debug(f"InvalidDicomError: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Diff failed: {type(e).__name__}: {e}", file=sys.stderr)
        logger.debug(f"Exception during diff: {e}", exc_info=True)
        return 1




def setup_parser(subparsers):
    """Setup argument parser for diff command."""
    parser = subparsers.add_parser('diff', help='Compare two DICOM files')
    parser.add_argument('before', help='Original DICOM file')
    parser.add_argument('after', help='Modified DICOM file')
    parser.add_argument('-u', '--show-unchanged', action='store_true',
                        help='Show unchanged tags')
    parser.add_argument('--fail-on-changes', action='store_true',
                        help='Exit with error if any changes found')
    parser.set_defaults(func=diff_command)
