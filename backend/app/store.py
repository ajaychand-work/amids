"""
Compatibility wrapper for older imports.

The canonical implementations now live in backend.app.services.storage_service.
"""

from .services.storage_service import (
    append_feedback,
    append_prediction,
    compute_metrics,
    load_feedback,
    load_predictions,
    load_roadmap,
)

__all__ = [
    "load_roadmap",
    "load_feedback",
    "load_predictions",
    "append_feedback",
    "append_prediction",
    "compute_metrics",
]
