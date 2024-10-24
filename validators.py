from typing import Union, Tuple, Optional
from dataclasses import dataclass
from PyQt6.QtGui import QValidator, QDoubleValidator
from PyQt6.QtCore import Qt

@dataclass
class ValidationRange:
    """Represents a valid range for numeric inputs"""
    minimum: float
    maximum: float
    decimals: int = 4

class CNCParameterValidator(QDoubleValidator):
    """Base validator for CNC parameter inputs with customizable range and precision"""
    def __init__(
            self,
            minimum: float,
            maximum: float,
            decimals: int = 4,
            parent = None
    ):
        super().__init__(minimum, maximum, decimals, parent)
        self.setNotation(QDoubleValidator.Notation.StandardNotation)

    def validate(self, input_str: str, pos: int) -> Tuple[QValidator.State, str, int]:
        """
        Validates the input string and ensures it meets the parameter requirements

        Args:
            input_str: The string to validate
            pos: Current cursor position

        Returns:
            Tuple containing validation state, validated string, and cursor position
        """
        if not input_str:
            return QValidator.State.Intermediate, input_str, pos

        try:
            value = float(input_str)
            if value < self.bottom() or value > self.top():
                return QValidator.State.Invalid, input_str, pos
            return QValidator.State.Acceptable, input_str, pos
        except ValueError:
            return QValidator.State.Invalid, input_str, pos

class FlutesValidator(CNCParameterValidator):
    """Validator for number of flutes input"""
    def __init__(self, parent=None):
        super().__init__(1, 8, 0, parent)  # Whole numbers between 1 and 8 flutes

    def validate(self, input_str: str, pos: int) -> Tuple[QValidator.State, str, int]:
        """Additional validation to ensure whole numbers only"""
        state, string, pos = super().validate(input_str, pos)
        if state != QValidator.State.Acceptable:
            return state, string, pos

        try:
            value = float(input_str)
            if value.is_integer():
                return QValidator.State.Acceptable, string, pos
            return QValidator.State.Invalid, string, pos
        except ValueError:
            return QValidator.State.Invalid, string, pos

class DiameterValidator(CNCParameterValidator):
    """Validator for tool diameter input"""
    def __init__(self, parent=None):
        super().__init__(0.1, 25.4, 3, parent)  # 0.1mm to 1 inch (25.4mm)

class CutDepthValidator(CNCParameterValidator):
    """Validator for depth of cut (DOC) input"""
    def __init__(self, tool_diameter: float, parent=None):
        max_doc = tool_diameter * 3  # Maximum DOC is typically 3x tool diameter
        super().__init__(0.01, max_doc, 3, parent)

class CutWidthValidator(CNCParameterValidator):
    """Validator for width of cut (WOC) input"""
    def __init__(self, tool_diameter: float, parent=None):
        super().__init__(0.01, tool_diameter, 3, parent)  # Maximum WOC is tool diameter

class ChiploadValidator(CNCParameterValidator):
    """Validator for chipload input based on material and tool properties"""
    def __init__(self, material_type: str, tool_diameter: float, num_flutes: int, parent=None):
        # Get chipload range for material and tool
        from calculations import suggest_chipload  # Import here to avoid circular imports
        min_chipload, max_chipload = suggest_chipload(tool_diameter, material_type)

        # Convert to total chipload (per flute * number of flutes)
        total_min = min_chipload * num_flutes
        total_max = max_chipload * num_flutes

        super().__init__(total_min, total_max, 4, parent)

def validate_cutting_parameters(
        flutes: float,
        diameter: float,
        woc: float,
        doc: float,
        chipload: float,
        material_type: str
) -> Tuple[bool, Optional[str]]:
    """
    Validates all cutting parameters together to ensure they form a valid combination

    Args:
        flutes: Number of flutes
        diameter: Tool diameter in mm
        woc: Width of cut in mm
        doc: Depth of cut in mm
        chipload: Total chipload in mm
        material_type: Type of material being cut

    Returns:
        Tuple of (is_valid: bool, error_message: Optional[str])
    """
    # Validate flutes
    if not FlutesValidator().validate(str(flutes), 0)[0] == QValidator.State.Acceptable:
        return False, "Invalid number of flutes"

    # Validate diameter
    if not DiameterValidator().validate(str(diameter), 0)[0] == QValidator.State.Acceptable:
        return False, "Invalid tool diameter"

    # Validate WOC
    if not CutWidthValidator(diameter).validate(str(woc), 0)[0] == QValidator.State.Acceptable:
        return False, "Invalid width of cut"

    # Validate DOC
    if not CutDepthValidator(diameter).validate(str(doc), 0)[0] == QValidator.State.Acceptable:
        return False, "Invalid depth of cut"

    # Validate chipload
    if not ChiploadValidator(material_type, diameter, int(flutes)).validate(
            str(chipload), 0
    )[0] == QValidator.State.Acceptable:
        return False, "Invalid chipload for material and tool combination"

    # Additional combination checks
    if woc > diameter:
        return False, "Width of cut cannot exceed tool diameter"

    if doc > diameter * 3:
        return False, "Depth of cut cannot exceed 3x tool diameter"

    return True, None