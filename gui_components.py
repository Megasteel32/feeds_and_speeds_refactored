#!/usr/bin/env python3

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QPushButton, QGroupBox,
                             QGridLayout)
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import pyqtSignal

class InputGroup(QGroupBox):
    """Widget containing all input fields for the CNC calculator."""

    inputChanged = pyqtSignal()  # Signal emitted when any input changes

    def __init__(self, parent=None):
        super().__init__("Inputs", parent)
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # Create input fields
        self.flutes = self.create_input("Number of endmill flutes:", 1, 0, 0)
        self.tool_diameter = self.create_input("Endmill diameter (mm):", 6.35, 1, 0)

        # RPM Selection
        self.rpm_label = QLabel("RPM:")
        self.layout.addWidget(self.rpm_label, 2, 0)
        self.rpm_combo = QComboBox()
        self.rpm_combo.addItems(["10000", "14000", "18000", "23000", "27000", "32000"])
        self.rpm_combo.setCurrentText("18000")
        self.rpm_combo.currentTextChanged.connect(self.inputChanged.emit)
        self.rpm_combo.setMinimumHeight(30)
        self.layout.addWidget(self.rpm_combo, 2, 1)

        self.woc = self.create_input("Width of cut (WOC) (mm):", 6.35, 3, 0)
        self.doc = self.create_input("Depth of cut (DOC) (mm):", 0.254, 4, 0)

        # Material Selection
        self.material_label = QLabel("Material type:")
        self.layout.addWidget(self.material_label, 5, 0)
        self.material_combo = QComboBox()
        self.material_combo.addItems([
            "Soft plastics",
            "Soft wood & hard plastics",
            "Hard wood & aluminium"
        ])
        self.material_combo.currentTextChanged.connect(self.inputChanged.emit)
        self.material_combo.setMinimumHeight(30)
        self.layout.addWidget(self.material_combo, 5, 1)

        # Cutting Style Selection
        self.cutting_style_label = QLabel("Cutting style:")
        self.layout.addWidget(self.cutting_style_label, 6, 0)
        self.cutting_style_combo = QComboBox()
        self.cutting_style_combo.addItems(["Wide and Shallow", "Narrow and Deep"])
        self.cutting_style_combo.setMinimumHeight(30)
        self.layout.addWidget(self.cutting_style_combo, 6, 1)

        # Chipload suggestion label
        self.chipload_suggestion = QLabel()
        self.chipload_suggestion.setWordWrap(True)
        self.layout.addWidget(self.chipload_suggestion, 7, 0, 1, 2)

        # Chipload input
        self.chipload = self.create_input("Target total chipload (mm):", 0.0254, 8, 0)

    def create_input(self, label, default, row, col):
        """Helper method to create a labeled input field."""
        label_widget = QLabel(label)
        self.layout.addWidget(label_widget, row, col)
        input_widget = QLineEdit(str(default))
        input_widget.setValidator(QDoubleValidator())
        input_widget.textChanged.connect(self.inputChanged.emit)
        input_widget.setMinimumHeight(30)
        self.layout.addWidget(input_widget, row, col + 1)
        return input_widget

    def get_values(self):
        """Returns a dictionary of all input values."""
        return {
            'flutes': float(self.flutes.text()),
            'tool_diameter': float(self.tool_diameter.text()),
            'rpm': float(self.rpm_combo.currentText()),
            'woc': float(self.woc.text()),
            'doc': float(self.doc.text()),
            'chipload': float(self.chipload.text()),
            'material': self.material_combo.currentText(),
            'cutting_style': self.cutting_style_combo.currentText()
        }

class ResultsGroup(QGroupBox):
    """Widget displaying calculation results."""

    def __init__(self, parent=None):
        super().__init__("Results", parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Create result fields
        self.feedrate_result = self.create_output("Required feedrate (mm/min):")
        self.woc_guideline = self.create_output("WOC guideline (mm):")
        self.doc_guideline = self.create_output("DOC guideline (mm):")
        self.plunge_rate_guideline = self.create_output("Plunge rate guideline (mm/min):")

        # Warning label
        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("color: red; font-weight: bold;")
        self.warning_label.setWordWrap(True)
        self.layout.addWidget(self.warning_label)

    def create_output(self, label):
        """Helper method to create a labeled output field."""
        output_layout = QHBoxLayout()
        label_widget = QLabel(label)
        output_layout.addWidget(label_widget)
        output_widget = QLineEdit()
        output_widget.setReadOnly(True)
        output_widget.setMinimumHeight(30)
        output_layout.addWidget(output_widget)
        self.layout.addLayout(output_layout)
        return output_widget

    def update_results(self, feedrate=None, warnings=None, guidelines=None):
        """Update all result fields with new values."""
        if feedrate is not None:
            self.feedrate_result.setText(f"{feedrate:.0f}")

        if warnings:
            self.warning_label.setText(warnings)
        else:
            self.warning_label.setText("")

        if guidelines:
            self.woc_guideline.setText(guidelines.get('woc', ''))
            self.doc_guideline.setText(guidelines.get('doc', ''))
            self.plunge_rate_guideline.setText(guidelines.get('plunge_rate', ''))

class ControlPanel(QWidget):
    """Widget containing control buttons."""

    calculateClicked = pyqtSignal()
    maximizeClicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        # Create buttons
        calculate_button = QPushButton("Calculate")
        calculate_button.clicked.connect(self.calculateClicked.emit)
        calculate_button.setMinimumHeight(35)
        self.layout.addWidget(calculate_button)

        maximize_button = QPushButton("Maximize Feedrate")
        maximize_button.clicked.connect(self.maximizeClicked.emit)
        maximize_button.setMinimumHeight(35)
        self.layout.addWidget(maximize_button)