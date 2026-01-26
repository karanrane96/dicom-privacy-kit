"""CLI command for anonymizing DICOM files."""

import argparse
import logging
import sys
from pathlib import Path
from pydicom import dcmread, dcmwrite
from pydicom.errors import InvalidDicomError
from ..anonymizer import AnonymizationEngine, generate_compliance_report, format_report

logger = logging.getLogger(__name__)


def anonymize_command(args):
    """Execute anonymization command.
    
    Returns:
        0 on success, 1 on failure
    """
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path.with_suffix('.anonymized.dcm')
    
    # Validate input file exists
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        return 1
    
    try:
        # Load DICOM file
        print(f"Loading: {input_path}")
        dataset = dcmread(str(input_path))
        logger.debug(f"Loaded DICOM file with {len(dataset)} elements")
        
        # Anonymize
        engine = AnonymizationEngine(salt=args.salt or "")
        print(f"Applying profile: {args.profile}")
        anonymized = engine.anonymize(dataset, args.profile)
        logger.debug(f"Anonymized dataset has {len(anonymized)} elements")
        
        # Validate output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save
        dcmwrite(str(output_path), anonymized)
        print(f"Saved: {output_path}")
        
        # Show log
        if args.verbose:
            print("\nAnonymization Log:")
            log_entries = engine.get_log()
            if log_entries:
                for entry in log_entries:
                    print(f"  {entry}")
            else:
                print("  (no log entries)")
        
        # Generate report
        if args.report:
            report = generate_compliance_report(dataset, anonymized)
            print(f"\nCOMPLIANCE REPORT:")
            print(f"  Total PHI tags: {report.total_phi_tags}")
            print(f"  Processed: {report.removed_phi_tags}")
            print(f"  Remaining: {report.remaining_phi_tags}")
            print(f"  Compliance: {report.compliance_percentage:.1f}%")
            print(f"\n{format_report(report)}")
            
            if report.remaining_tags and not args.ignore_remaining:
                print(f"\nWARNING: {len(report.remaining_tags)} PHI tags remain")
                return 1
        
        print(f"\nSUCCESS: Anonymization complete")
        return 0
        
    except InvalidDicomError as e:
        print(f"ERROR: Invalid DICOM file: {e}", file=sys.stderr)
        logger.debug(f"InvalidDicomError: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Anonymization failed: {type(e).__name__}: {e}", file=sys.stderr)
        logger.debug(f"Exception during anonymization: {e}", exc_info=True)
        return 1




def setup_parser(subparsers):
    """Setup argument parser for anonymize command."""
    parser = subparsers.add_parser('anonymize', help='Anonymize a DICOM file')
    parser.add_argument('input', help='Input DICOM file')
    parser.add_argument('-o', '--output', help='Output file (default: input.anonymized.dcm)')
    parser.add_argument('-p', '--profile', default='basic', help='Anonymization profile (default: basic)')
    parser.add_argument('-s', '--salt', help='Salt for hashing')
    parser.add_argument('-r', '--report', action='store_true', help='Generate compliance report')
    parser.add_argument('--ignore-remaining', action='store_true', help='Exit 0 even if PHI tags remain')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show detailed log')
    parser.set_defaults(func=anonymize_command)
