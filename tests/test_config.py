"""Tests for configuration loading and validation."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_example_config_exists():
    """Test that example configuration files exist."""
    config_dir = Path(__file__).parent.parent / "config" / "example"
    assert config_dir.exists()
    assert config_dir.is_dir()

    default_config = config_dir / "default.cfg"
    assert default_config.exists()
    assert default_config.is_file()


def test_config_parsing():
    """Test basic configuration parsing."""
    import core.config as config

    config_path = Path(__file__).parent.parent / "config" / "example" / "default.cfg"

    # This should not raise an exception
    cfg = config.load(str(config_path))
    assert cfg is not None
    assert isinstance(cfg, dict)


def test_config_has_required_sections():
    """Test that config has required global section."""
    import core.config as config

    config_path = Path(__file__).parent.parent / "config" / "example" / "default.cfg"
    cfg = config.load(str(config_path))

    # Check for global section
    assert "global" in cfg
