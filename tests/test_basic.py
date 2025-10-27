"""Basic smoke tests for qudi."""

import sys


def test_python_version():
    """Test that we're running Python 3.13+."""
    assert sys.version_info >= (3, 13), f"Python 3.13+ required, got {sys.version_info}"


def test_imports():
    """Test that core dependencies can be imported."""
    import numpy
    import packaging
    import scipy

    assert numpy.__version__
    assert scipy.__version__
    assert packaging.version
