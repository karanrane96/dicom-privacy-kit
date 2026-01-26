"""Element value comparison utilities for DICOM diff."""

import logging

logger = logging.getLogger(__name__)


def normalize_element_value(elem):
    """Normalize DICOM element value for comparison.
    
    This function converts element values to normalized forms suitable for
    comparison, accounting for:
    - VR (Value Representation) specific normalization
    - Numeric value normalization (e.g., 1.0 == 1)
    - Date/time normalization
    - Binary data handling
    
    Args:
        elem: pydicom DataElement
    
    Returns:
        Normalized value suitable for comparison
    """
    try:
        if elem is None or elem.value is None:
            return None
        
        value = elem.value
        vr = elem.VR if hasattr(elem, 'VR') else None
        
        # Handle numeric VRs - normalize to numeric values
        if vr in ('DS', 'IS', 'US', 'SS', 'UL', 'SL', 'FD', 'FL'):
            try:
                # Try to convert to float for numeric comparison
                if isinstance(value, (list, tuple)):
                    return tuple(float(v) if v else 0.0 for v in value)
                else:
                    return float(value) if value else 0.0
            except (ValueError, TypeError) as e:
                logger.debug(f"Could not convert value to float (VR={vr}): {e}, using string representation")
        
        # Handle date/time VRs - normalize to string
        if vr in ('DA', 'TM', 'DT'):
            # Ensure consistent string representation
            return str(value) if value else ""
        
        # Handle binary VRs - use binary comparison
        if vr in ('OB', 'OW', 'OD', 'OF', 'OL', 'OV'):
            # Binary data should be compared as-is
            if isinstance(value, bytes):
                return value
            return bytes(str(value), 'utf-8') if value else b''
        
        # Handle sequences - compare element by element
        if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
            try:
                # For sequences, return comparable representation
                return tuple(normalize_element_value(v) if hasattr(v, 'VR') else v 
                           for v in value)
            except (TypeError, AttributeError) as e:
                logger.debug(f"Could not normalize sequence/iterable (VR={vr}): {e}, using string representation")
        
        # Default: string representation (preserve whitespace for comparison)
        return str(value) if value else ""
    
    except Exception:
        # On any error, fall back to string representation
        return str(elem.value) if elem else ""


def elements_are_equal(elem1, elem2):
    """Compare two DICOM elements for value equality.
    
    Uses normalized element values to properly compare:
    - Numeric values (1 == 1.0)
    - Date/time values
    - Binary data
    - Sequences
    
    Args:
        elem1: First pydicom DataElement (or None)
        elem2: Second pydicom DataElement (or None)
    
    Returns:
        True if elements have equal values, False otherwise
    """
    # Handle None/missing elements
    if elem1 is None and elem2 is None:
        return True
    if elem1 is None or elem2 is None:
        return False
    
    try:
        # Normalize values for comparison
        val1 = normalize_element_value(elem1)
        val2 = normalize_element_value(elem2)
        
        # Direct comparison
        if val1 == val2:
            return True
        
        # Handle floating point comparison with tolerance
        if isinstance(val1, float) and isinstance(val2, float):
            import math
            return math.isclose(val1, val2, rel_tol=1e-9)
        
        # Handle tuple of floats (multi-valued numeric)
        if isinstance(val1, tuple) and isinstance(val2, tuple):
            if len(val1) != len(val2):
                return False
            import math
            return all(
                math.isclose(v1, v2, rel_tol=1e-9) if isinstance(v1, float) else v1 == v2
                for v1, v2 in zip(val1, val2)
            )
        
        return False
    
    except Exception:
        # On comparison error, return False
        return False
