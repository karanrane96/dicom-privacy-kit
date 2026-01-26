"""DICOM tag registry and metadata definitions."""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class DicomTag:
    """DICOM tag metadata."""
    tag: str
    name: str
    vr: str  # Value Representation
    vm: str  # Value Multiplicity
    is_phi: bool = False
    risk_level: int = 0  # 0-5 scale


# DICOM tag registry - subset of commonly used tags
# Using pydicom keywords as keys
TAG_REGISTRY: Dict[str, DicomTag] = {
    "PatientName": DicomTag("PatientName", "PatientName", "PN", "1", is_phi=True, risk_level=5),
    "PatientID": DicomTag("PatientID", "PatientID", "LO", "1", is_phi=True, risk_level=5),
    "PatientBirthDate": DicomTag("PatientBirthDate", "PatientBirthDate", "DA", "1", is_phi=True, risk_level=4),
    "PatientSex": DicomTag("PatientSex", "PatientSex", "CS", "1", is_phi=False, risk_level=1),
    "StudyDate": DicomTag("StudyDate", "StudyDate", "DA", "1", is_phi=True, risk_level=3),
    "StudyTime": DicomTag("StudyTime", "StudyTime", "TM", "1", is_phi=True, risk_level=2),
    "StudyInstanceUID": DicomTag("StudyInstanceUID", "StudyInstanceUID", "UI", "1", is_phi=True, risk_level=4),
    "SeriesInstanceUID": DicomTag("SeriesInstanceUID", "SeriesInstanceUID", "UI", "1", is_phi=True, risk_level=4),
}


def get_tag_metadata(tag: str) -> Optional[DicomTag]:
    """Retrieve metadata for a DICOM tag."""
    return TAG_REGISTRY.get(tag)


def get_phi_tags() -> List[str]:
    """Return list of all PHI tags."""
    return [tag for tag, meta in TAG_REGISTRY.items() if meta.is_phi]
