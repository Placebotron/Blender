from abc import ABC, abstractmethod
from typing import Optional
import trimesh

class DetectionResult:
    def __init__(self, label: str, confidence: float, rationale: str):
        self.label = label
        self.confidence = confidence
        self.rationale = rationale

class ShapeDetector(ABC):
    """Return DetectionResult or None if the detector is unsure."""
    @abstractmethod
    def detect(self, mesh: trimesh.Trimesh, node_attrs: dict) -> Optional[DetectionResult]:
        ...
