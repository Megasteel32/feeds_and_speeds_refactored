from dataclasses import dataclass
from typing import Optional, Tuple, Callable
from PyQt6.QtWidgets import QMessageBox
from calculations import calculate_feedrate, suggest_chipload

@dataclass
class CalculationParameters:
    flutes: float
    tool_diameter: float
    rpm: float
    woc: float
    doc: float
    chipload: float
    material: str
    cutting_style: str

@dataclass
class CalculationResults:
    feedrate: float
    woc_range: str
    doc_range: str
    plunge_rate: str
    warning: str = ""

class EventHandler:
    """Handles business logic for the CNC Calculator application."""

    def __init__(self, update_ui_callback: Callable[[CalculationResults], None]):
        """
        Initialize the event handler.

        Args:
            update_ui_callback: Callback function to update the UI with calculation results
        """
        self.update_ui = update_ui_callback
        self._feedrate_limit = 6000  # mm/min
        self._chipload_increment = 0.0001  # mm

    def handle_chipload_suggestion_update(self, tool_diameter: float, flutes: float, material: str) -> str:
        """
        Handle updating the chipload suggestion text.

        Args:
            tool_diameter: Tool diameter in mm
            flutes: Number of flutes
            material: Material type

        Returns:
            Suggested chipload range text
        """
        try:
            lower, upper = suggest_chipload(tool_diameter, material)
            per_flute = f"{lower:.4f} to {upper:.4f}"
            total = f"{lower * flutes:.4f} to {upper * flutes:.4f}"
            return f"Suggested chipload range:\n{per_flute} mm per flute\n{total} mm total"
        except ValueError:
            return "Invalid input. Please enter valid numbers."

    def handle_calculation(self, params: CalculationParameters) -> CalculationResults:
        """
        Handle the main calculation workflow.

        Args:
            params: Calculation parameters

        Returns:
            Calculation results
        """
        try:
            feedrate = calculate_feedrate(
                params.flutes,
                params.rpm,
                params.chipload,
                params.woc,
                params.tool_diameter
            )

            warning = ""
            if feedrate > self._feedrate_limit:
                warning = f"Warning: Calculated feedrate exceeds {self._feedrate_limit} mm/min"

            guidelines = self._calculate_guidelines(
                params.tool_diameter,
                feedrate,
                params.cutting_style,
                params.material
            )

            return CalculationResults(
                feedrate=feedrate,
                woc_range=guidelines['woc_range'],
                doc_range=guidelines['doc_range'],
                plunge_rate=guidelines['plunge_rate'],
                warning=warning
            )

        except ValueError as e:
            raise ValueError(f"Calculation failed: {str(e)}")

    def handle_feedrate_maximization(self, params: CalculationParameters,
                                     increase_rpm_callback: Callable[[], None]) -> Optional[CalculationResults]:
        """
        Handle the feedrate maximization workflow.

        Args:
            params: Calculation parameters
            increase_rpm_callback: Callback to increase RPM in the UI

        Returns:
            Calculation results or None if maximization fails
        """
        try:
            lower_chipload, upper_chipload = suggest_chipload(params.tool_diameter, params.material)
            lower_total_chipload = lower_chipload * params.flutes
            upper_total_chipload = upper_chipload * params.flutes

            max_result = self._find_maximum_feedrate(
                params, lower_total_chipload, upper_total_chipload)

            if max_result is None:
                return None

            feedrate, max_chipload = max_result

            # Check if we've reached the maximum suggested chipload
            if abs(max_chipload - upper_total_chipload) < self._chipload_increment:
                if self._should_increase_rpm():
                    increase_rpm_callback()
                    return None

            guidelines = self._calculate_guidelines(
                params.tool_diameter,
                feedrate,
                params.cutting_style,
                params.material
            )

            return CalculationResults(
                feedrate=feedrate,
                woc_range=guidelines['woc_range'],
                doc_range=guidelines['doc_range'],
                plunge_rate=guidelines['plunge_rate']
            )

        except ValueError as e:
            raise ValueError(f"Maximization failed: {str(e)}")

    def _find_maximum_feedrate(self, params: CalculationParameters,
                               lower_chipload: float, upper_chipload: float) -> Optional[Tuple[float, float]]:
        """
        Find the maximum valid feedrate within chipload constraints.

        Returns:
            Tuple of (max_feedrate, max_chipload) or None if no valid feedrate found
        """
        current_chipload = lower_chipload
        max_feedrate = 0
        max_chipload = current_chipload

        while current_chipload <= upper_chipload:
            per_flute_chipload = current_chipload / params.flutes
            feedrate = calculate_feedrate(
                params.flutes,
                params.rpm,
                per_flute_chipload,
                params.woc,
                params.tool_diameter
            )

            if max_feedrate < feedrate <= self._feedrate_limit:
                max_feedrate = feedrate
                max_chipload = current_chipload
            elif feedrate > self._feedrate_limit:
                break

            current_chipload += self._chipload_increment

        if max_feedrate == 0:
            return None

        return max_feedrate, max_chipload

    def _calculate_guidelines(self, tool_diameter: float, feedrate: float,
                              cutting_style: str, material: str) -> dict:
        """
        Calculate cutting guidelines based on parameters.

        Returns:
            Dictionary containing WOC, DOC, and plunge rate guidelines
        """
        # WOC and DOC calculations based on cutting style
        if cutting_style == "Wide and Shallow":
            woc_range = f"{tool_diameter * 0.4:.2f} to {tool_diameter:.2f}"
            doc_range = f"{tool_diameter * 0.05:.2f} to {tool_diameter * 0.1:.2f}"
        else:  # Narrow and Deep
            woc_range = f"{tool_diameter * 0.1:.2f} to {tool_diameter * 0.25:.2f}"
            doc_range = f"{tool_diameter:.2f} to {tool_diameter * 3:.2f}"

        # Plunge rate calculations based on material
        if material == "Hard wood & aluminium":
            plunge_rate = f"{feedrate * 0.1:.0f} to {feedrate * 0.3:.0f}"
        elif material == "Soft wood & hard plastics":
            plunge_rate = f"{feedrate * 0.3:.0f}"
        else:  # Soft plastics
            plunge_rate = f"{feedrate * 0.4:.0f} to {feedrate * 0.5:.0f}"

        return {
            'woc_range': woc_range,
            'doc_range': doc_range,
            'plunge_rate': f"{plunge_rate} mm/min"
        }

    def _should_increase_rpm(self) -> bool:
        """
        Ask user if they want to increase RPM.

        Returns:
            True if user wants to increase RPM, False otherwise
        """
        response = QMessageBox.question(
            None,
            "Maximizer Result",
            "Maximum feedrate achieved at maximum suggested chipload.\n"
            "Would you like to increase the RPM to the next step?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return response == QMessageBox.StandardButton.Yes


class ValidationHandler:
    """Handles input validation for the CNC Calculator."""

    @staticmethod
    def validate_calculation_parameters(params: CalculationParameters) -> None:
        """
        Validate calculation parameters.

        Args:
            params: Parameters to validate

        Raises:
            ValueError: If any parameter is invalid
        """
        if params.flutes <= 0:
            raise ValueError("Number of flutes must be positive")
        if params.tool_diameter <= 0:
            raise ValueError("Tool diameter must be positive")
        if params.rpm <= 0:
            raise ValueError("RPM must be positive")
        if params.woc <= 0:
            raise ValueError("Width of cut must be positive")
        if params.doc <= 0:
            raise ValueError("Depth of cut must be positive")
        if params.chipload <= 0:
            raise ValueError("Chipload must be positive")
        if params.woc > params.tool_diameter:
            raise ValueError("Width of cut cannot exceed tool diameter")