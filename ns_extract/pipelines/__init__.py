"""Pipeline implementations for extracting information from papers."""

from .participant_demographics import ParticipantDemographicsExtractor
from .umls_disease import UMLSDiseaseExtractor
from .nv_task import TaskExtractor
from .base import Pipeline, IndependentPipeline, DependentPipeline, Extractor
from .api import APIPromptExtractor
from .tfidf import TFIDFExtractor

# Public API
__all__ = [
    "ParticipantDemographicsExtractor",
    "TaskExtractor",
    "Pipeline",
    "IndependentPipeline", 
    "DependentPipeline",
    "Extractor",
    "APIPromptExtractor",
    "TFIDFExtractor",
    "UMLSDiseaseExtractor",
]

# Version for API compatibility
__version__ = "1.0.0"
