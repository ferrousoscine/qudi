{
  description = "Qudi-fork - Python 3.13 development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    nixpkgs,
    flake-utils,
    ...
  }:
    flake-utils.lib.eachSystem ["x86_64-linux"] (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};

        # Build fysom package (not in nixpkgs)
        fysom = pkgs.python313Packages.buildPythonPackage rec {
          pname = "fysom";
          version = "2.1.6";
          format = "setuptools";

          src = pkgs.fetchPypi {
            inherit pname version;
            sha256 = "sha256-42F7efGSIMcrHH5p1NbCo2qAzb6A9N973rq1q0yJO/U=";
          };

          doCheck = false;

          meta = with pkgs.lib; {
            description = "Finite State Machine for Python";
            homepage = "https://github.com/mriehl/fysom";
            license = licenses.mit;
          };
        };

        # Python dependencies for qudi
        pythonDeps = with pkgs.python313Packages;
          [
            # Core scientific computing
            numpy
            scipy
            matplotlib
            lxml

            # Configuration and state management
            pyyaml
            ruamel-yaml
            packaging

            # Qt GUI framework
            qtpy
            pyqt5

            # Data analysis and fitting
            lmfit
            h5py
            pillow
            pyqtgraph

            # Jupyter/IPython support
            jupyter
            ipykernel
            ipython
            pyzmq
            tornado
            qtconsole
            ipywidgets

            # Remote procedure calls
            rpyc

            # Version control
            gitpython

            # Development tools
            pytest
            pytest-qt
            pytest-cov
            mypy
            setuptools
            wheel
          ]
          ++ [fysom];

        # Development environment
        devEnv = pkgs.python313.withPackages (_ps: pythonDeps);
      in {
        packages = {
          default = devEnv;
          python-env = devEnv;
        };

        checks = {
          pytest = pkgs.stdenv.mkDerivation {
            name = "qudi-tests";
            src = ./.;
            buildInputs = [devEnv];
            buildPhase = ''
              export PYTHONPATH="$PWD:''${PYTHONPATH:-}"
              export HOME=$TMPDIR
              ${devEnv}/bin/pytest tests/ -v --tb=short
            '';
            installPhase = ''
              mkdir -p $out
              echo "Tests passed" > $out/result
            '';
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            devEnv
            pkgs.uv
            pkgs.gh
            pkgs.just
            pkgs.ruff
            pkgs.alejandra
            pkgs.git

            # Qt platform plugins and dependencies
            pkgs.qt5.qtbase
            pkgs.qt5.qtsvg

            # X11 dependencies for Qt GUI
            pkgs.xorg.libX11
            pkgs.xorg.libXext
            pkgs.xorg.libXrender
            pkgs.xorg.libxcb
            pkgs.xorg.xcbutil
            pkgs.xorg.xcbutilwm
            pkgs.xorg.xcbutilimage
            pkgs.xorg.xcbutilkeysyms
            pkgs.xorg.xcbutilrenderutil
            pkgs.libGL
          ];

          shellHook = ''
            echo "Qudi Python 3.13 development environment"
            echo "Python version: $(python3 --version)"
            echo ""

            # Set Qt platform and plugin path
            export QT_QPA_PLATFORM=xcb
            export QT_QPA_PLATFORM_PLUGIN_PATH="${pkgs.qt5.qtbase.bin}/lib/qt-${pkgs.qt5.qtbase.version}/plugins"
            export QT_PLUGIN_PATH="${pkgs.qt5.qtbase.bin}/lib/qt-${pkgs.qt5.qtbase.version}/plugins"
            export QT_XCB_GL_INTEGRATION=none

            # Add current directory to PYTHONPATH
            export PYTHONPATH="$PWD:''${PYTHONPATH:-}"

            echo ""
            echo "Available commands (via justfile):"
            just --list
          '';
        };

        apps = {
          default = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "qudi" ''
              set -euo pipefail
              export PYTHONPATH="$PWD:''${PYTHONPATH:-}"
              export QT_QPA_PLATFORM=xcb
              export QT_QPA_PLATFORM_PLUGIN_PATH="${pkgs.qt5.qtbase.bin}/lib/qt-${pkgs.qt5.qtbase.version}/plugins"
              export QT_PLUGIN_PATH="${pkgs.qt5.qtbase.bin}/lib/qt-${pkgs.qt5.qtbase.version}/plugins"
              export QT_XCB_GL_INTEGRATION=none
              exec ${devEnv}/bin/python3 start.py "$@"
            ''}/bin/qudi";
            meta = {
              description = "Run Qudi application";
            };
          };

          headless = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "qudi-headless" ''
              set -euo pipefail
              export PYTHONPATH="$PWD:''${PYTHONPATH:-}"
              exec ${devEnv}/bin/python3 start.py --no-gui "$@"
            ''}/bin/qudi-headless";
            meta = {
              description = "Run Qudi application without GUI";
            };
          };

          install-kernel = {
            type = "app";
            program = "${pkgs.writeShellScriptBin "install-kernel" ''
              set -euo pipefail
              export PYTHONPATH="$PWD:''${PYTHONPATH:-}"
              exec ${devEnv}/bin/python3 core/qudikernel.py install
            ''}/bin/install-kernel";
            meta = {
              description = "Install Qudi Jupyter kernel";
            };
          };
        };

        formatter = pkgs.alejandra;
      }
    );
}
