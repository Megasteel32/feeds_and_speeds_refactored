from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Union, Literal
from enum import Enum

class MaterialType(str, Enum):
    SOFT_PLASTICS = "Soft plastics"
    SOFT_WOOD_HARD_PLASTICS = "Soft wood & hard plastics"
    HARD_WOOD_ALUMINIUM = "Hard wood & aluminium"

class CuttingStyle(str, Enum):
    WIDE_SHALLOW = "Wide and Shallow"
    NARROW_DEEP = "Narrow and Deep"

@dataclass
class MaterialProperties:
    """Represents the properties and chipload ranges for different materials."""
    chiploads: Dict[MaterialType, Dict[float, Tuple[float, float]]]

    def __post_init__(self):
        # Default chipload data
        if not hasattr(self, 'chiploads') or not self.chiploads:
            self.chiploads = {
                MaterialType.SOFT_PLASTICS: {
                    1.5: (0.05, 0.075),
                    3.175: (0.05, 0.13),
                    6: (0.05, 0.254)
                },
                MaterialType.SOFT_WOOD_HARD_PLASTICS: {
                    1.5: (0.025, 0.04),
                    3.175: (0.025, 0.063),
                    6: (0.025, 0.127)
                },
                MaterialType.HARD_WOOD_ALUMINIUM: {
                    1.5: (0.013, 0.013),
                    3.175: (0.013, 0.025),
                    6: (0.025, 0.05)
                }
            }

    def get_chipload_range(self, material: MaterialType, tool_diameter: float) -> Tuple[float, float]:
        """
        Get the recommended chipload range for a specific material and tool diameter.
        Args:
            material: The type of material being cut
            tool_diameter: The diameter of the cutting tool in mm
        Returns:
            Tuple of (min_chipload, max_chipload) in mm
        """
        material_data = self.chiploads[material]
        diameters = sorted(material_data.keys())

        if tool_diameter <= diameters[0]:
            return material_data[diameters[0]]
        elif tool_diameter >= diameters[-1]:
            return self._extrapolate_chipload(material, tool_diameter)
        else:
            return self._interpolate_chipload(material, tool_diameter)

    def _interpolate_chipload(self, material: MaterialType, tool_diameter: float) -> Tuple[float, float]:
        """Interpolate chipload values for a given tool diameter."""
        material_data = self.chiploads[material]
        diameters = sorted(material_data.keys())

        lower_diameter = max(d for d in diameters if d <= tool_diameter)
        upper_diameter = min(d for d in diameters if d >= tool_diameter)

        if lower_diameter == upper_diameter:
            return material_data[lower_diameter]

        lower_range = material_data[lower_diameter]
        upper_range = material_data[upper_diameter]

        return (
            self._interpolate(tool_diameter, lower_diameter, lower_range[0], upper_diameter, upper_range[0]),
            self._interpolate(tool_diameter, lower_diameter, lower_range[1], upper_diameter, upper_range[1])
        )

    def _extrapolate_chipload(self, material: MaterialType, tool_diameter: float) -> Tuple[float, float]:
        """Extrapolate chipload values for tool diameters larger than the maximum reference diameter."""
        material_data = self.chiploads[material]
        diameters = sorted(material_data.keys())

        lower_diameter, upper_diameter = diameters[-2], diameters[-1]
        lower_range = material_data[lower_diameter]
        upper_range = material_data[upper_diameter]

        slope_lower = (upper_range[0] - lower_range[0]) / (upper_diameter - lower_diameter)
        slope_upper = (upper_range[1] - lower_range[1]) / (upper_diameter - lower_diameter)

        extrapolated_lower = upper_range[0] + slope_lower * (tool_diameter - upper_diameter)
        extrapolated_upper = upper_range[1] + slope_upper * (tool_diameter - upper_diameter)

        # Ensure we don't go below the minimum recommended chipload
        extrapolated_lower = max(extrapolated_lower, material_data[diameters[0]][0])

        return extrapolated_lower, extrapolated_upper

    @staticmethod
    def _interpolate(x: float, x1: float, y1: float, x2: float, y2: float) -> float:
        """Linear interpolation helper function."""
        return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

@dataclass
class CuttingParameters:
    """Represents the cutting parameters for a CNC operation."""
    flutes: int
    tool_diameter: float  # mm
    rpm: int
    width_of_cut: float  # mm
    depth_of_cut: float  # mm
    chipload: float  # mm
    material: MaterialType
    cutting_style: CuttingStyle

    def __post_init__(self):
        self.validate()

    def validate(self):
        """Validate the cutting parameters."""
        if self.flutes <= 0:
            raise ValueError("Number of flutes must be positive")
        if self.tool_diameter <= 0:
            raise ValueError("Tool diameter must be positive")
        if self.rpm <= 0:
            raise ValueError("RPM must be positive")
        if self.width_of_cut <= 0:
            raise ValueError("Width of cut must be positive")
        if self.depth_of_cut <= 0:
            raise ValueError("Depth of cut must be positive")
        if self.chipload <= 0:
            raise ValueError("Chipload must be positive")

@dataclass
class CalculationResults:
    """Represents the results of cutting parameter calculations."""
    feedrate: float  # mm/min
    woc_min: float  # mm
    woc_max: float  # mm
    doc_min: float  # mm
    doc_max: float  # mm
    plunge_rate_min: Optional[float] = None  # mm/min
    plunge_rate_max: Optional[float] = None  # mm/min
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        self._validate_results()

    def _validate_results(self):
        """Validate calculation results and add warnings if necessary."""
        if self.feedrate > 10000:
            self.warnings.append("Calculated feedrate exceeds 10,000 mm/min")
        if self.woc_max < self.woc_min:
            self.warnings.append("Invalid WOC range")
        if self.doc_max < self.doc_min:
            self.warnings.append("Invalid DOC range")
        if None not in (self.plunge_rate_min, self.plunge_rate_max):
            if self.plunge_rate_max < self.plunge_rate_min:
                self.warnings.append("Invalid plunge rate range")

    def get_woc_guideline(self) -> str:
        """Format WOC guideline for display."""
        return f"{self.woc_min:.2f} to {self.woc_max:.2f}"

    def get_doc_guideline(self) -> str:
        """Format DOC guideline for display."""
        return f"{self.doc_min:.2f} to {self.doc_max:.2f}"

    def get_plunge_rate_guideline(self) -> str:
        """Format plunge rate guideline for display."""
        if self.plunge_rate_min is None or self.plunge_rate_max is None:
            return "N/A"
        if self.plunge_rate_min == self.plunge_rate_max:
            return f"{self.plunge_rate_min:.0f}"
        return f"{self.plunge_rate_min:.0f} to {self.plunge_rate_max:.0f}"