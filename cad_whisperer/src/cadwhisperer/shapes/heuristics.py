# ─────────────────────────────────────────────────────────────────────────────
# cadwhisperer/shapes/heuristics.py
# ─────────────────────────────────────────────────────────────────────────────
"""A zoo of rule‑based detectors – fast, no ML deps."""
from typing import Optional
import trimesh
from .base import DetectionResult, ShapeDetector
from cadwhisperer.utils.geometry import (
    is_cylinder_like, flatness, aspect_ratio, has_hex_symmetry)

# ---------- Screw / Bolt ---------------------------------------------------- #
class ScrewDetector(ShapeDetector):
    KEYWORDS = {"screw", "bolt", "thread", "vis", "schraube"}

    def detect(self, mesh: trimesh.Trimesh, attrs: dict) -> Optional[DetectionResult]:
        name = attrs.get("label", "").lower()
        if any(k in name for k in self.KEYWORDS):
            return DetectionResult("SCREW", 0.95, "keyword match")
        if is_cylinder_like(mesh):
            return DetectionResult("SCREW", 0.65, "cylinder bbox")
        return None

# ---------- Plate ----------------------------------------------------------- #
class PlateDetector(ShapeDetector):
    def detect(self, mesh: trimesh.Trimesh, attrs: dict) -> Optional[DetectionResult]:
        if flatness(mesh) < 0.08 and aspect_ratio(mesh) > 3:
            return DetectionResult("PLATE", 0.8, "thin flat bbox")
        return None

# ---------- Pipe / Tube ----------------------------------------------------- #
class PipeDetector(ShapeDetector):
    def detect(self, mesh: trimesh.Trimesh, attrs: dict) -> Optional[DetectionResult]:
        if is_cylinder_like(mesh, min_ar=1.5):
            # Check for hollow: volume ≪ bbox volume
            vol = mesh.volume
            e0, e1, e2 = mesh.extents
            if vol / (e0 * e1 * e2) < 0.3:
                return DetectionResult("PIPE", 0.75, "hollow cylinder")
        return None

# ---------- Nut ------------------------------------------------------------- #
class NutDetector(ShapeDetector):
    KEYWORDS = {"nut"}
    def detect(self, mesh: trimesh.Trimesh, attrs: dict) -> Optional[DetectionResult]:
        name = attrs.get("label", "").lower()
        if any(k in name for k in self.KEYWORDS):
            return DetectionResult("NUT", 0.9, "keyword match")
        if has_hex_symmetry(mesh):
            return DetectionResult("NUT", 0.7, "hexagonal symmetry")
        return None

# ---------- Wheel ----------------------------------------------------------- #
class WheelDetector(ShapeDetector):
    KEYWORDS = {"wheel", "rad"}
    def detect(self, mesh: trimesh.Trimesh, attrs: dict) -> Optional[DetectionResult]:
        name = attrs.get("label", "").lower()
        if any(k in name for k in self.KEYWORDS):
            return DetectionResult("WHEEL", 0.9, "keyword match")
        # Round + thick → ratio checks
        from cadwhisperer.utils.geometry import bbox_extents
        e0, e1, e2 = bbox_extents(mesh)
        if 0.9 <= e1 / e0 <= 1.1 and 0.2 <= e2 / e0 <= 0.6:
            return DetectionResult("WHEEL", 0.6, "disk‑like bbox")
        return None

# registry
ALL_HEURISTIC_DETECTORS = [
    ScrewDetector(), PlateDetector(), PipeDetector(), NutDetector(), WheelDetector()
]
