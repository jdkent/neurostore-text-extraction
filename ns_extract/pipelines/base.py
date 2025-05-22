"""Base pipeline and extraction functionality (Legacy Support).

This module provides backwards compatibility for the existing codebase while
encouraging migration to the new modular structure. New code should use the
components from ns_extract.pipelines.core and ns_extract.pipelines.utils.

Deprecation Notice:
This module will be maintained for compatibility but may be removed in version 2.0.
"""

from __future__ import annotations

import warnings

# Import from new locations
from .core.extractor import BaseExtractor as Extractor
from .core.pipeline import Pipeline
from .core.pipeline import (
    IndependentPipeline,
    DependentPipeline
)

# Re-export for backwards compatibility
__all__ = [
    "Pipeline",
    "IndependentPipeline", 
    "DependentPipeline",
    "Extractor"
]


def show_deprecation_warning():
    warnings.warn(
        "The 'base' module is deprecated and will be removed in version 2.0. "
        "Please update your imports to use 'ns_extract.pipelines.core' instead.",
        DeprecationWarning,
        stacklevel=2
    )


# Trigger deprecation warning on module import
show_deprecation_warning()


# Maintain aliases for backwards compatibility while providing new paths
Pipeline = Pipeline
IndependentPipeline = IndependentPipeline  
DependentPipeline = DependentPipeline
Extractor = Extractor
