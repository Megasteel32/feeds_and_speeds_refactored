from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Tuple, Optional, Union, TypeAlias
from decimal import Decimal

# Type aliases for clarity and consistency
Millimeters: TypeAlias = Decimal
RPM: TypeAlias = int
FeedRate: TypeAlias = float
ChipLoad: TypeAlias = float
MaterialName: TypeAlias = str
DiameterRange: TypeAlias = Dict[float, Tuple[float, float]]

# Enums for categorical data
class MaterialType(Enum):
    SOFT_PLASTICS = "Soft plastics"
    SOFT_WOOD_HARD_PLASTICS = "Soft wood & hard plastics"
    HARD_WOOD_ALUMINIUM = "Hard wood & aluminium"

    @classmethod
    def get_display_name(cls, value: str) -> str:
        """Convert enum value to display name."""
        return value

class CuttingStyle(Enum):
    WIDE_SHALLOW = "Wide and Shallow"
    NARROW_DEEP = "Narrow and Deep"

class ValidationStatus(Enum):
    VALID = auto()
    INVALID_NUMBER = auto()
    OUT_OF_RANGE = auto()
    MISSING_REQUIRED = auto()

# Data structures for tool and cutting parameters
@dataclass
class ToolParameters:
    flutes: int
    diameter: Millimeters
    rpm: RPM

    def __post_init__(self):
        self.flutes = int(self.flutes)
        self.diameter = Decimal(str(self.diameter))
        self.rpm = int(self.rpm)

@dataclass
class CutParameters:
    width_of_cut: Millimeters
    depth_of_cut: Millimeters
    chipload: ChipLoad
    material_type: MaterialType
    cutting_style: CuttingStyle

    def __post_init__(self):
        self.width_of_cut = Decimal(str(self.width_of_cut))
        self.depth_of_cut = Decimal(str(self.depth_of_cut))
        self.chipload = float(self.chipload)

@dataclass
class CalculationResult:
    feedrate: FeedRate
    woc_guideline: Tuple[Millimeters, Millimeters]
    doc_guideline: Tuple[Millimeters, Millimeters]
    plunge_rate_range: Tuple[FeedRate, FeedRate]
    warnings: Optional[str] = None

@dataclass
class ChiploadRange:
    lower: ChipLoad
    upper: ChipLoad
    per_flute: bool = True

    def to_total_chipload(self, flutes: int) -> 'ChiploadRange':
        """Convert per-flute chipload to total chipload."""
        if self.per_flute:
            return ChiploadRange(
                lower=self.lower * flutes,
                upper=self.upper * flutes,
                per_flute=False
            )
        return self

    def to_per_flute_chipload(self, flutes: int) -> 'ChiploadRange':
        """Convert total chipload to per-flute chipload."""
        if not self.per_flute:
            return ChiploadRange(
                lower=self.lower / flutes,
                upper=self.upper / flutes,
                per_flute=True
            )
        return self

# Custom exceptions
class ValidationError(Exception):
    def __init__(self, field: str, status: ValidationStatus, message: str):
        self.field = field
        self.status = status
        self.message = message
        super().__init__(message)

class CalculationError(Exception):
    """Raised when a calculation fails due to invalid inputs or mathematical errors."""
    pass

# Type guards and validation functions
def is_valid_rpm(rpm: int) -> bool:
    """Check if RPM is within valid range."""
    return 0 < rpm <= 32000

def is_valid_tool_diameter(diameter: Union[float, Decimal]) -> bool:
    """Check if tool diameter is within valid range."""
    return 0 < float(diameter) <= 25.4  # Max 1 inch in mm

def is_valid_chipload(chipload: float, material_type: MaterialType, tool_diameter: float) -> bool:
    """Check if chipload is within valid range for material and tool diameter."""
    try:
        range_data = get_chipload_range(material_type, tool_diameter)
        return range_data.lower <= chipload <= range_data.upper
    except:
        return False

def get_chipload_range(material_type: MaterialType, tool_diameter: float) -> ChiploadRange:
    """Get valid chipload range for given material and tool diameter."""
    # Implementation would be moved from suggest_chipload function
    raise NotImplementedError("To be implemented based on suggest_chipload logic")