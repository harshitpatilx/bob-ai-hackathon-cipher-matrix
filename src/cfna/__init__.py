"""Cyber Fraud Network Analyzer (CFNA) - Bob-powered investigation toolkit."""

__version__ = "0.1.0"

from cfna.models import CaseBrief, CaseGraph, Entity, EntityType, Relation  # noqa: F401

__all__ = ["CaseGraph", "Entity", "EntityType", "Relation", "CaseBrief", "__version__"]
