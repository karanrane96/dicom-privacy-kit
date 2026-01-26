"""Anonymization engine - applies profiles to DICOM datasets."""

from typing import List, Optional
from pydicom import Dataset
from ..core.profiles import ProfileRule, get_profile
from ..core.actions import Action, ACTION_HANDLERS
from ..core.utils import clone_dataset, hash_value


class AnonymizationEngine:
    """Engine for applying anonymization profiles to DICOM datasets."""
    
    def __init__(self, salt: str = ""):
        """Initialize the engine with an optional salt for hashing."""
        self.salt = salt
        self.log: List[str] = []
    
    def anonymize(
        self,
        dataset: Dataset,
        profile: str | List[ProfileRule],
        in_place: bool = False
    ) -> Dataset:
        """
        Apply anonymization profile to a dataset.
        
        Args:
            dataset: DICOM dataset to anonymize
            profile: Profile name or list of rules
            in_place: Modify dataset in place or return copy
        
        Returns:
            Anonymized DICOM dataset
        """
        if not in_place:
            dataset = clone_dataset(dataset)
        
        # Get rules
        if isinstance(profile, str):
            rules = get_profile(profile)
        else:
            rules = profile
        
        self.log = []
        
        for rule in rules:
            self._apply_rule(dataset, rule)
        
        return dataset
    
    def _apply_rule(self, dataset: Dataset, rule: ProfileRule) -> None:
        """Apply a single anonymization rule."""
        tag = rule.tag
        action = rule.action
        
        if action == Action.REMOVE:
            ACTION_HANDLERS[Action.REMOVE](dataset, tag)
            self.log.append(f"REMOVED: {tag}")
        
        elif action == Action.HASH:
            hash_fn = lambda val: hash_value(val, self.salt)
            ACTION_HANDLERS[Action.HASH](dataset, tag, hash_fn)
            self.log.append(f"HASHED: {tag}")
        
        elif action == Action.EMPTY:
            ACTION_HANDLERS[Action.EMPTY](dataset, tag)
            self.log.append(f"EMPTIED: {tag}")
        
        elif action == Action.KEEP:
            self.log.append(f"KEPT: {tag}")
        
        elif action == Action.REPLACE:
            ACTION_HANDLERS[Action.REPLACE](dataset, tag, rule.replacement_value)
            self.log.append(f"REPLACED: {tag} -> {rule.replacement_value}")
    
    def get_log(self) -> List[str]:
        """Return the anonymization log."""
        return self.log
