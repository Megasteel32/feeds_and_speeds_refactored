"""
Core calculation module for CNC milling parameters.

This module provides classes and functions for calculating various CNC milling parameters
including feedrates, chiploads, and related calculations. It encapsulates the core business
logic separate from the GUI.
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional
import math


@dataclass
class MaterialProperties:
    """Represents the chipload properties for different materials and tool diameters."""
    name: str
    chipload_ranges: Dict[float, Tuple[float, float]]

    @classmethod
    def get_default_materials(cls) -> Dict[str, 'MaterialProperties']:
        """Creates and returns the default set of material properties."""
        return {
            "Soft plastics": cls(
                name="Soft plastics",
                chipload_ranges={
                    1.5: (0.05, 0.075),
                    3.175: (0.05, 0.13),
                    6: (0.05, 0.254)
                }
            ),
            "Soft wood & hard plastics": cls(
                name="Soft wood & hard plastics",
                chipload_ranges={
                    1.5: (0.025, 0.04),
                    3.175: (0.025, 0.063),
                    6: (0.025, 0.127)
                }
            ),
            "Hard wood & aluminium": cls(
                name="Hard wood & aluminium",
                chipload_ranges={
                    1.5: (0.013, 0.013),
                    3.175: (0.013, 0.025),
                    6: (0.025, 0.05)
                }
            )
        }


@dataclass
class CuttingParameters:
    """Represents the parameters for a cutting operation."""
    flutes: float
    tool_diameter: float
    rpm: float
    width_of_cut: float
    depth_of_cut: float
    chipload: float

    def validate(self) -> Optional[str]:
        """
        Validates the cutting parameters.
        Returns None if valid, error message string if invalid.
        """
        if self.flutes <= 0:
            return "Number of flutes must be positive"
        if self.tool_diameter <= 0:
            return "Tool diameter must be positive"
        if self.rpm <= 0:
            return "RPM must be positive"
        if self.width_of_cut <= 0:
            return "Width of cut must be positive"
        if self.depth_of_cut <= 0:
            return "Depth of cut must be positive"
        if self.chipload <= 0:
            return "Chipload must be positive"
        if self.width_of_cut > self.tool_diameter:
            return "Width of cut cannot exceed tool diameter"
        return None


class ChiploadCalculator:
    """Handles calculations related to chiploads and feedrates."""

    def __init__(self):
        self.materials = MaterialProperties.get_default_materials()

    def calculate_feedrate(self, params: CuttingParameters) -> float:
        """
        Calculate the feedrate based on cutting parameters.

        Args:
            params: CuttingParameters object containing cutting parameters

        Returns:
            float: Calculated feedrate in mm/min
        """
        validation_error = params.validate()
        if validation_error:
            raise ValueError(validation_error)

        base_feedrate = params.rpm * params.chipload * params.flutes

        if params.width_of_cut > params.tool_diameter / 2:
            return base_feedrate
        else:
            return base_feedrate / math.sqrt(
                1 - (1 - 2 * params.width_of_cut / params.tool_diameter) ** 2
            )

    def _interpolate(self, x: float, x1: float, y1: float, x2: float, y2: float) -> float:
        """
        Linear interpolation helper function.

        Args:
            x: Value to interpolate for
            x1: First x value
            y1: First y value
            x2: Second x value
            y2: Second y value

        Returns:
            float: Interpolated value
        """
        return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

    def suggest_chipload(self, tool_diameter: float, material_type: str) -> Tuple[float, float]:
        """
        Suggests a chipload range based on tool diameter and material.

        Args:
            tool_diameter: Diameter of the tool in mm
            material_type: Type of material being cut

        Returns:
            Tuple[float, float]: Suggested (minimum, maximum) chipload values in mm

        Raises:
            ValueError: If material_type is not recognized
        """
        if material_type not in self.materials:
            raise ValueError(f"Unknown material type: {material_type}")

        material = self.materials[material_type]
        diameters = sorted(material.chipload_ranges.keys())

        # Handle small tool diameters
        if tool_diameter <= diameters[0]:
            return material.chipload_ranges[diameters[0]]

        # Handle large tool diameters with extrapolation
        if tool_diameter >= diameters[-1]:
            lower_diameter, upper_diameter = diameters[-2], diameters[-1]
            lower_range = material.chipload_ranges[lower_diameter]
            upper_range = material.chipload_ranges[upper_diameter]

            slope_lower = (upper_range[0] - lower_range[0]) / (upper_diameter - lower_diameter)
            slope_upper = (upper_range[1] - lower_range[1]) / (upper_diameter - lower_diameter)

            extrapolated_lower = upper_range[0] + slope_lower * (tool_diameter - upper_diameter)
            extrapolated_upper = upper_range[1] + slope_upper * (tool_diameter - upper_diameter)

            # Ensure we don't go below the minimum chipload
            extrapolated_lower = max(extrapolated_lower, material.chipload_ranges[diameters[0]][0])

            return extrapolated_lower, extrapolated_upper

        # Handle intermediate tool diameters with interpolation
        lower_diameter = max(d for d in diameters if d <= tool_diameter)
        upper_diameter = min(d for d in diameters if d >= tool_diameter)

        if lower_diameter == upper_diameter:
            return material.chipload_ranges[lower_diameter]

        lower_range = material.chipload_ranges[lower_diameter]
        upper_range = material.chipload_ranges[upper_diameter]

        interpolated_lower = self._interpolate(
            tool_diameter, lower_diameter, lower_range[0], upper_diameter, upper_range[0]
        )
        interpolated_upper = self._interpolate(
            tool_diameter, lower_diameter, lower_range[1], upper_diameter, upper_range[1]
        )

        return interpolated_lower, interpolated_upper


class CuttingGuidelineCalculator:
    """Calculates cutting guidelines based on tool and material parameters."""

    @staticmethod
    def calculate_woc_range(tool_diameter: float, cutting_style: str) -> Tuple[float, float]:
        """
        Calculate the recommended width of cut range.

        Args:
            tool_diameter: Tool diameter in mm
            cutting_style: Either "Wide and Shallow" or "Narrow and Deep"

        Returns:
            Tuple[float, float]: (min_woc, max_woc) in mm
        """
        if cutting_style == "Wide and Shallow":
            return (tool_diameter * 0.4, tool_diameter)
        else:  # Narrow and Deep
            return (tool_diameter * 0.1, tool_diameter * 0.25)

    @staticmethod
    def calculate_doc_range(tool_diameter: float, cutting_style: str) -> Tuple[float, float]:
        """
        Calculate the recommended depth of cut range.

        Args:
            tool_diameter: Tool diameter in mm
            cutting_style: Either "Wide and Shallow" or "Narrow and Deep"

        Returns:
            Tuple[float, float]: (min_doc, max_doc) in mm
        """
        if cutting_style == "Wide and Shallow":
            return (tool_diameter * 0.05, tool_diameter * 0.1)
        else:  # Narrow and Deep
            return (tool_diameter, tool_diameter * 3)

    @staticmethod
    def calculate_plunge_rate_range(feedrate: float, material_type: str) -> Tuple[float, float]:
        """
        Calculate the recommended plunge rate range.

        Args:
            feedrate: Calculated feedrate in mm/min
            material_type: Type of material being cut

        Returns:
            Tuple[float, float]: (min_plunge_rate, max_plunge_rate) in mm/min
        """
        if material_type == "Hard wood & aluminium":
            return (feedrate * 0.1, feedrate * 0.3)
        elif material_type == "Soft wood & hard plastics":
            return (feedrate * 0.3, feedrate * 0.3)
        else:  # Soft plastics
            return (feedrate * 0.4, feedrate * 0.5)