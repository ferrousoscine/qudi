_default:
    @just --list

# Update flake inputs
update:
    nix flake update

# Run all CI checks locally
ci: check fmt lint test

# Check the Nix flake
check:
    @nix flake check --all-systems

# Format all code (Python with ruff, Nix with alejandra)
fmt:
    ruff format .
    alejandra -q .

# Lint Python code with ruff
lint:
    ruff check .

# Fix linting issues automatically
fix:
    ruff check --fix .

# Run Python tests
test:
    pytest tests/ -v

# Run type checking with mypy
typecheck:
    mypy core/ logic/ gui/ hardware/ --ignore-missing-imports

# Enter development shell
dev:
    nix develop

# Build the project
build:
    nix build

# Clean build artifacts
clean:
    rm -rf result .pytest_cache .ruff_cache .mypy_cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete

# Install Jupyter kernel
install-kernel:
    python3 core/qudikernel.py install

# Run qudi
run *ARGS:
    nix run . -- {{ ARGS }}

# Run qudi without GUI
run-headless *ARGS:
    nix run .#headless -- {{ ARGS }}
