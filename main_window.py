#!/usr/bin/env python3

import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from gui_components import InputGroup, ResultsGroup, ControlPanel
from calculations import calculate_feedrate, suggest_chipload
from data_models import CuttingParameters, CalculationResults
from config import APP_TITLE, WINDOW_GEOMETRY, BASE_FONT_SIZE


class CNCCalculatorGUI(QMainWindow):
    """
    Main window class for the CNC Calculator application.
    Manages the high-level layout and coordination between components.
    """

    def __init__(self):
        super().__init__()
        self.init_window()
        self.setup_components()
        self.connect_signals()

    def init_window(self):
        """Initialize the main window properties."""
        self.setWindowTitle(APP_TITLE)
        self.setGeometry(*WINDOW_GEOMETRY)

        # Set up application-wide font
        app = QApplication.instance()
        font = app.font()
        font.setPointSize(BASE_FONT_SIZE)
        app.setFont(font)

        # Create and set central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

    def setup_components(self):
        """Create and arrange the main UI components."""
        # Create component instances
        self.input_group = InputGroup()
        self.control_panel = ControlPanel()
        self.results_group = ResultsGroup()

        # Add components to main layout
        self.main_layout.addWidget(self.input_group)
        self.main_layout.addWidget(self.control_panel)
        self.main_layout.addWidget(self.results_group)

    def connect_signals(self):
        """Connect signals between components."""
        # Connect control panel buttons to calculation methods
        self.control_panel.calculate_button.clicked.connect(self.calculate)
        self.control_panel.maximize_button.clicked.connect(self.maximize_feedrate)

        # Connect input changes to update suggestions
        self.input_group.tool_diameter.textChanged.connect(self.update_chipload_suggestion)
        self.input_group.material_combo.currentTextChanged.connect(self.update_chipload_suggestion)
        self.input_group.rpm_combo.currentTextChanged.connect(self.update_chipload_suggestion)

    def calculate(self):
        """Handle the calculate button click."""
        try:
            # Get cutting parameters from input group
            params = self.input_group.get_cutting_parameters()

            # Perform calculations
            feedrate = calculate_feedrate(
                params.flutes,
                params.rpm,
                params.chipload,
                params.width_of_cut,
                params.tool_diameter
            )

            # Update results
            results = CalculationResults(
                feedrate=feedrate,
                tool_diameter=params.tool_diameter,
                material=params.material,
                cutting_style=params.cutting_style
            )

            self.results_group.update_results(results)

        except ValueError as e:
            self.results_group.show_error("Invalid input: " + str(e))

    def maximize_feedrate(self):
        """Handle the maximize feedrate button click."""
        try:
            # Get cutting parameters
            params = self.input_group.get_cutting_parameters()

            # Get chipload range for material
            lower_chipload, upper_chipload = suggest_chipload(
                params.tool_diameter,
                params.material
            )

            # Calculate maximum feedrate (implementation moved to calculations.py)
            max_results = self.calculate_maximum_feedrate(params, lower_chipload, upper_chipload)

            # Update UI with results
            self.input_group.set_chipload(max_results.optimal_chipload)
            self.results_group.update_results(max_results)

            # Handle RPM increase suggestion if needed
            if max_results.suggest_rpm_increase:
                self.handle_rpm_increase_suggestion(max_results.feedrate)

        except ValueError as e:
            self.results_group.show_error("Invalid input: " + str(e))

    def update_chipload_suggestion(self):
        """Update the chipload suggestion based on current inputs."""
        try:
            params = self.input_group.get_cutting_parameters()
            lower, upper = suggest_chipload(params.tool_diameter, params.material)
            self.input_group.update_chipload_suggestion(lower, upper, params.flutes)
        except ValueError:
            self.input_group.clear_chipload_suggestion()

    def handle_rpm_increase_suggestion(self, current_feedrate):
        """Handle suggesting RPM increase to user."""
        if self.results_group.confirm_rpm_increase(current_feedrate):
            self.input_group.increase_rpm()
            self.maximize_feedrate()


def main():
    app = QApplication(sys.argv)
    window = CNCCalculatorGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()