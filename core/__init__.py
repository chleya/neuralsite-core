# -*- coding: utf-8 -*-
"""
NeuralSite Core
公路参数化几何计算引擎
"""

from .engine import NeuralSiteEngine, Coordinate3D, LODConfig, create_engine_from_json
from .geometry import (
    HorizontalAlignment, VerticalAlignment, CrossSectionCalculator,
    LineElement, CircularCurveElement, SpiralCurveElement,
    VerticalCurveElement, CrossSectionTemplate
)


__version__ = "1.0.0"
__author__ = "NeuralSite Team"


__all__ = [
    'NeuralSiteEngine', 'Coordinate3D', 'LODConfig', 'create_engine_from_json',
    'HorizontalAlignment', 'VerticalAlignment', 'CrossSectionCalculator',
    'LineElement', 'CircularCurveElement', 'SpiralCurveElement',
    'VerticalCurveElement', 'CrossSectionTemplate',
]
