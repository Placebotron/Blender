# ─────────────────────────────────────────────────────────────────────────────
# cadwhisperer/utils/geometry.py
# ─────────────────────────────────────────────────────────────────────────────
"""Geometry helper functions shared by all detectors."""
from __future__ import annotations
import numpy as np
import trimesh

EPS = 1e-6

def bbox_extents(mesh: trimesh.Trimesh) -> np.ndarray:  # (3,) sorted
    if not isinstance(mesh, trimesh.Trimesh):
        raise TypeError("Expected Trimesh")
    ext = np.sort(mesh.bounds[1] - mesh.bounds[0])
    return ext + EPS

def is_cylinder_like(mesh: trimesh.Trimesh, *, min_ar: float = 2.5) -> bool:
    """True if the mesh’s bbox looks like a long cylinder."""
    e0, e1, e2 = bbox_extents(mesh)
    return 0.8 <= e1 / e0 <= 1.25 and e2 / e1 >= min_ar

def flatness(mesh: trimesh.Trimesh) -> float:
    """Thickness / longest‑edge ratio (≈0 for plates)."""
    e0, e1, e2 = bbox_extents(mesh)
    return e0 / e2  # smallest / largest

def aspect_ratio(mesh: trimesh.Trimesh) -> float:
    """Longest / middle dimension."""
    e0, e1, e2 = bbox_extents(mesh)
    return e2 / e1

def has_hex_symmetry(mesh: trimesh.Trimesh, *, tol: float = 0.05) -> bool:
    """Crude: radially sample cross‑section, check six‑fold repeats."""
    try:
        slice = mesh.section(plane_origin=mesh.centroid, plane_normal=[0, 0, 1])
        if slice is None:
            return False
        poly = slice.to_planar()[0]  # returns (poly, tf)
        r = np.linalg.norm(poly.vertices, axis=1)
        r_mean = r.mean()
        max_dev = np.abs(r - r_mean).max()
        return max_dev / r_mean < tol
    except Exception:
        return False

