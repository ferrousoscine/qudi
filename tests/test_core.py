"""Tests for core qudi functionality."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_core_imports():
    """Test that core modules can be imported."""
    import core.config
    import core.connector
    import core.interface
    import core.module

    assert core.config
    assert core.connector
    assert core.interface
    assert core.module


def test_util_imports():
    """Test that utility modules can be imported."""
    import core.util.helpers
    import core.util.math
    import core.util.mutex
    import core.util.network

    assert core.util.helpers
    assert core.util.math
    assert core.util.mutex
    assert core.util.network


def test_interface_imports():
    """Test that interface modules can be imported."""
    import interface.camera_interface
    import interface.confocal_scanner_interface
    import interface.microwave_interface
    import interface.simple_data_interface

    assert interface.camera_interface
    assert interface.confocal_scanner_interface
    assert interface.microwave_interface
    assert interface.simple_data_interface


def test_qt_imports():
    """Test that Qt dependencies are available."""
    from qtpy import QtCore, QtGui, QtWidgets

    assert QtCore
    assert QtGui
    assert QtWidgets


def test_scientific_stack():
    """Test scientific Python stack."""
    import lmfit
    import matplotlib
    import numpy as np
    import scipy

    # Basic numpy operations
    arr = np.array([1, 2, 3, 4, 5])
    assert arr.mean() == 3.0
    assert arr.std() > 0

    # Check versions
    assert matplotlib.__version__
    assert lmfit.__version__
    assert scipy.__version__


def test_yaml_config():
    """Test YAML configuration loading."""
    import yaml

    # Test basic YAML parsing
    yaml_str = """
    test:
      value: 42
      name: "test"
    """
    data = yaml.safe_load(yaml_str)
    assert data["test"]["value"] == 42
    assert data["test"]["name"] == "test"


def test_pathlib_usage():
    """Test modern pathlib usage (Python 3.13 idiom)."""
    from pathlib import Path

    # Test that we can use pathlib
    test_path = Path(__file__)
    assert test_path.exists()
    assert test_path.is_file()
    assert test_path.parent.name == "tests"
