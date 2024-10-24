from dataclasses import dataclass
from typing import Dict, Tuple, List
from enum import Enum


class MaterialType(str, Enum):
    SOFT_PLASTICS = "Soft plastics"
    SOFT_WOOD_HARD_PLASTICS = "Soft wood & hard plastics"
    HARD_WOOD_ALUMINIUM = "Hard wood & aluminium"


class CuttingStyle(str, Enum):
    WIDE_SHALLOW = "Wide and Shallow"
    NARROW_DEEP = "Narrow and Deep"


@dataclass
class UISettings:
    WINDOW_WIDTH: int = 600
    WINDOW_HEIGHT: int = 400
    WINDOW_X_POS: int = 200
    WINDOW_Y_POS: int = 200
    BASE_FONT_SIZE: int = 16
    MIN_INPUT_HEIGHT: int = 30
    BUTTON_HEIGHT: int = 35
    WARNING_COLOR: str = "color: red; font-weight: bold;"


@dataclass
class DefaultValues:
    FLUTES: float = 1.0
    TOOL_DIAMETER: float = 6.35  # mm
    DEFAULT_RPM: str = "18000"
    WOC: float = 6.35  # mm
    DOC: float = 0.254  # mm
    CHIPLOAD: float = 0.0254  # mm
    MAX_FEEDRATE: float = 6000.0  # mm/min
    CHIPLOAD_INCREMENT: float = 0.0001  # mm


class CuttingParameters:
    # Chipload ranges for different materials and tool diameters
    CHIPLOADS: Dict[str, Dict[float, Tuple[float, float]]] = {
        MaterialType.SOFT_PLASTICS: {
            1.5: (0.05, 0.075),
            3.175: (0.05, 0.13),
            6.0: (0.05, 0.254)
        },
        MaterialType.SOFT_WOOD_HARD_PLASTICS: {
            1.5: (0.025, 0.04),
            3.175: (0.025, 0.063),
            6.0: (0.025, 0.127)
        },
        MaterialType.HARD_WOOD_ALUMINIUM: {
            1.5: (0.013, 0.013),
            3.175: (0.013, 0.025),
            6.0: (0.025, 0.05)
        }
    }

    # Standard tool diameters for interpolation
    STANDARD_DIAMETERS: List[float] = [1.5, 3.175, 6.0]

    # Cutting style guidelines as percentage of tool diameter
    CUTTING_GUIDELINES = {
        CuttingStyle.WIDE_SHALLOW: {
            "woc_min": 0.4,  # 40% of tool diameter
            "woc_max": 1.0,  # 100% of tool diameter
            "doc_min": 0.05,  # 5% of tool diameter
            "doc_max": 0.1,   # 10% of tool diameter
        },
        CuttingStyle.NARROW_DEEP: {
            "woc_min": 0.1,   # 10% of tool diameter
            "woc_max": 0.25,  # 25% of tool diameter
            "doc_min": 1.0,   # 100% of tool diameter
            "doc_max": 3.0,   # 300% of tool diameter
        }
    }

    # Plunge rate guidelines as percentage of feedrate
    PLUNGE_RATE_GUIDELINES = {
        MaterialType.HARD_WOOD_ALUMINIUM: (0.1, 0.3),      # 10-30% of feedrate
        MaterialType.SOFT_WOOD_HARD_PLASTICS: (0.3, 0.3),  # 30% of feedrate
        MaterialType.SOFT_PLASTICS: (0.4, 0.5)             # 40-50% of feedrate
    }


class RPMSettings:
    AVAILABLE_RPMS: List[str] = [
        "10000",
        "14000",
        "18000",
        "23000",
        "27000",
        "32000"
    ]


class Labels:
    WINDOW_TITLE = "CNC Milling Calculator"
    INPUT_GROUP = "Inputs"
    RESULTS_GROUP = "Results"

    # Input labels
    FLUTES_LABEL = "Number of endmill flutes:"
    TOOL_DIAMETER_LABEL = "Endmill diameter (mm):"
    RPM_LABEL = "RPM:"
    WOC_LABEL = "Width of cut (WOC) (mm):"
    DOC_LABEL = "Depth of cut (DOC) (mm):"
    MATERIAL_LABEL = "Material type:"
    CUTTING_STYLE_LABEL = "Cutting style:"
    CHIPLOAD_LABEL = "Target total chipload (mm):"

    # Button labels
    CALCULATE_BUTTON = "Calculate"
    MAXIMIZE_BUTTON = "Maximize Feedrate"

    # Results labels
    FEEDRATE_LABEL = "Required feedrate (mm/min):"
    WOC_GUIDELINE_LABEL = "WOC guideline (mm):"
    DOC_GUIDELINE_LABEL = "DOC guideline (mm):"
    PLUNGE_RATE_LABEL = "Plunge rate guideline (mm/min):"

    # Message strings
    INVALID_INPUT_MSG = "Invalid input. Please enter valid numbers."
    MAX_FEEDRATE_MSG = "Maximum feedrate of {feedrate:.0f} mm/min achieved."
    MAX_FEEDRATE_RPM_MSG = ("Maximum feedrate of {feedrate:.0f} mm/min achieved at maximum suggested chipload.\n"
                            "Would you like to increase the RPM to the next step?")
    RPM_LIMIT_MSG = "Already at maximum RPM."
    FEEDRATE_WARNING = "Warning: Calculated feedrate exceeds 6000 mm/min"
    MAXIMIZER_ERROR = "Unable to find a valid feedrate. Please check your inputs."