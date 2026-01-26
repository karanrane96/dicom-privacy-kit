"""CLI command for scoring PHI risk in DICOM files."""

import argparse
import logging
import sys
from pathlib import Path
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from ..risk import score_dataset, format_risk_score

logger = logging.getLogger(__name__)


def score_command(args):
    """Execute risk scoring command.
    
    Returns:
        0 on success (or if risk is acceptable), 1 on failure or high risk
    """
    input_path = Path(args.input)
    
    # Validate input file exists
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        return 1
    
    try:
        # Load DICOM file
        print(f"Loading: {input_path}")
        dataset = dcmread(str(input_path))
        logger.debug(f"Loaded DICOM file with {len(dataset)} elements")
        
        # Score
        print("Calculating PHI risk...")
        risk_score = score_dataset(dataset)
        logger.debug(f"Risk calculation complete: {risk_score.risk_percentage:.1f}%")
        
        # Display results
        print(f"\nRISK ASSESSMENT:")
        print(f"  Level: {risk_score.risk_level}")
        print(f"  Score: {risk_score.total_score:.1f} / {risk_score.max_score:.1f}")
        print(f"  Percentage: {risk_score.risk_percentage:.1f}%")
        print(f"  PHI tags found: {len(risk_score.tag_scores)}")
        
        print(f"\n{format_risk_score(risk_score)}")
        
        # Exit with error code if risk is high
        if args.fail_on_risk is not None:
            threshold = args.fail_on_risk
            if risk_score.risk_percentage >= threshold:
                print(f"\nERROR: Risk threshold exceeded: {risk_score.risk_percentage:.1f}% >= {threshold}%", file=sys.stderr)
                logger.debug(f"Risk threshold exceeded: {risk_score.risk_percentage:.1f}% >= {threshold}%")
                return 1
        
        print(f"\nSUCCESS: Risk assessment complete")
        return 0
        
    except InvalidDicomError as e:
        print(f"ERROR: Invalid DICOM file: {e}", file=sys.stderr)
        logger.debug(f"InvalidDicomError: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Scoring failed: {type(e).__name__}: {e}", file=sys.stderr)
        logger.debug(f"Exception during scoring: {e}", exc_info=True)
        return 1


def setup_parser(subparsers):
    """Setup argument parser for score command."""
    parser = subparsers.add_parser('score', help='Calculate PHI risk score')
    parser.add_argument('input', help='Input DICOM file')
    parser.add_argument('--fail-on-risk', type=float, metavar='PERCENT',
                        help='Exit with error if risk percentage exceeds threshold')
    parser.set_defaults(func=score_command)
