#!/usr/bin/env bash
set -euo pipefail

# Usage: ./setup.sh [PYTHON_VERSION]
# Example: ./setup.sh 3.11.4
# Default python version if not provided:
PYTHON_VERSION="${1:-3.11.4}"

# Project variables
PROJECT_DIR="${PWD}"
VENV_NAME="poker-cactus-${PYTHON_VERSION}"
BUILD_DIR="${PROJECT_DIR}/build"
SRC_DIR="${PROJECT_DIR}/cpp"
PY_PKG_DIR="${PROJECT_DIR}/python_package"

# Detect OS
OS="$(uname -s)"

echo "=== Setup started ==="
echo "Project dir: ${PROJECT_DIR}"
echo "Python version requested: ${PYTHON_VERSION}"
echo "Virtualenv name: ${VENV_NAME}"

# Helper: command exists
cmd_exists() { command -v "$1" >/dev/null 2>&1; }

# 1) Install system deps (apt or brew)
if [[ "$OS" == "Darwin" ]]; then
  echo "Detected macOS."
  if ! cmd_exists brew; then
    echo "Homebrew not found — please install Homebrew first: https://brew.sh/"
    echo "Aborting."
    exit 1
  fi

  echo "Installing system packages via brew..."
  brew update
  brew install pyenv pyenv-virtualenv cmake pkg-config coreutils
  # Xcode command line tools are required
  if ! xcode-select -p >/dev/null 2>&1; then
    echo "Installing Xcode command-line tools..."
    xcode-select --install || true
    echo "If installer didn't run, you may need to install Xcode tools manually."
  fi

elif [[ "$OS" == "Linux" ]] || [[ "$OS" == "FreeBSD" ]] || [[ "$OS" == "MINGW"* ]]; then
  echo "Detected Linux/Unix."
  if cmd_exists apt-get; then
    echo "Installing system packages via apt..."
    sudo apt-get update
    # Basic build deps + headers for compiling Python
    sudo apt-get install -y build-essential curl git cmake pkg-config \
      libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
      libffi-dev liblzma-dev
  else
    echo "Warning: automatic package installation not supported on this distro in the script."
    echo "Please ensure you have: build-essential (gcc/g++/make), curl, git, cmake, pkg-config, and development headers for zlib, openssl, readline, sqlite3, libffi, lzma installed."
  fi

else
  echo "Unsupported OS: ${OS}. Proceeding but you will need to make sure packages are installed manually."
fi

# 2) Install pyenv (if missing)
if ! cmd_exists pyenv; then
  echo "pyenv not found — installing pyenv..."
  # Use pyenv-installer (curl) recommended approach
  curl -fsSL https://pyenv.run | bash

  # Update shell rc files so pyenv is on PATH for this script run.
  export PYENV_ROOT="$HOME/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PATH"
  if ! echo "$SHELL" | grep -q "zsh"; then
    # assume bash
    SHELL_RC="$HOME/.bashrc"
  else
    SHELL_RC="$HOME/.zshrc"
  fi

  # Add pyenv init lines to shell rc if missing
  if ! grep -q 'pyenv init' "${SHELL_RC}" 2>/dev/null || true; then
    cat >> "${SHELL_RC}" <<'EOF'

# pyenv initialization (added by setup.sh)
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"
EOF
    echo "Appended pyenv init to ${SHELL_RC}. You may need to open a new shell to get pyenv in your PATH."
  fi

  # Load pyenv into current environment
  eval "$(pyenv init --path)" || true
  export PATH="$PYENV_ROOT/bin:$PATH"
fi

# Ensure pyenv-virtualenv plugin is available
if ! pyenv virtualenvs >/dev/null 2>&1; then
  echo "pyenv-virtualenv not available — attempting to install plugin..."
  # Clone plugin into pyenv plugins dir
  mkdir -p "$(pyenv root)"/plugins
  if [ ! -d "$(pyenv root)/plugins/pyenv-virtualenv" ]; then
    git clone https://github.com/pyenv/pyenv-virtualenv.git "$(pyenv root)/plugins/pyenv-virtualenv"
  fi
  eval "$(pyenv init --path)" || true
fi

# 3) Install requested Python version via pyenv if missing
if ! pyenv versions --bare | grep -q "^${PYTHON_VERSION}\$"; then
  echo "Installing Python ${PYTHON_VERSION} with pyenv (this can take a few minutes)..."
  # Allow build to use multiple jobs if env var MAKEFLAGS set; otherwise default
  # pyenv install options can vary. We'll call pyenv install.
  env PYTHON_CONFIGURE_OPTS="--enable-shared" pyenv install -v "${PYTHON_VERSION}"
else
  echo "Python ${PYTHON_VERSION} already installed with pyenv."
fi

# 4) Create virtualenv
if pyenv virtualenvs --bare | grep -q "^${VENV_NAME}\$"; then
  echo "Virtualenv ${VENV_NAME} already exists."
else
  echo "Creating pyenv virtualenv ${VENV_NAME}..."
  pyenv virtualenv "${PYTHON_VERSION}" "${VENV_NAME}"
fi

# Set local python version for this project (writes .python-version)
echo "${VENV_NAME}" > "${PROJECT_DIR}/.python-version"
echo ".python-version written with '${VENV_NAME}'."

# Activate the virtualenv in this script
# Note: pyenv-virtualenv provides 'pyenv activate' shell function.
# We can use pyenv shell for temporary activation in the script process:
pyenv shell "${VENV_NAME}"
echo "Activated pyenv virtualenv ${VENV_NAME} for this shell."

# 5) Upgrade pip and install Python build deps
echo "Upgrading pip and installing Python-side build deps..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install pybind11

# 6) Create C++/pybind11 skeleton (if not present)
if [ -d "${SRC_DIR}" ]; then
  echo "C++ source dir ${SRC_DIR} already exists — leaving files intact."
else
  echo "Creating C++ skeleton in ${SRC_DIR} ..."
  mkdir -p "${SRC_DIR}"
  cat > "${SRC_DIR}/CMakeLists.txt" <<'CMAKE'
cmake_minimum_required(VERSION 3.12)
project(cactus_eval)

# Find pybind11 (installed into the active Python environment)
find_package(pybind11 REQUIRED)

# Create the module
pybind11_add_module(cactus_eval module.cpp)

# Set C++ standard
target_compile_features(cactus_eval PRIVATE cxx_std_17)
CMAKE

  cat > "${SRC_DIR}/module.cpp" <<'CPP'
#include <pybind11/pybind11.h>
#include <vector>
#include <string>

namespace py = pybind11;

// Minimal placeholder: a very small and fast evaluator stub.
// Replace with full Cactus Kev evaluator implementation.
int evaluate_hand_stub(const std::vector<int>& cards) {
    // cards: vector of 5 (or 7) integers representing ranks/suits per your encoding
    // This stub returns -1 for invalid, otherwise a fake score
    if (cards.size() < 5) return -1;
    int s = 0;
    for (auto c : cards) s += c;
    return s;
}

PYBIND11_MODULE(cactus_eval, m) {
    m.doc() = "Cactus Kev style evaluator (skeleton) - replace evaluate_hand_stub with full implementation.";

    m.def("evaluate_hand", [](py::iterable py_cards) {
        std::vector<int> cards;
        for (auto item : py_cards) {
            cards.push_back(item.cast<int>());
        }
        int score = evaluate_hand_stub(cards);
        return score;
    }, "Evaluate a hand given a sequence of integer-encoded cards.");
}
CPP

  echo "Created C++ skeleton files."
fi

# 7) Create Python package wrapper to hold the built extension
if [ -d "${PY_PKG_DIR}" ]; then
  echo "Python packaging directory ${PY_PKG_DIR} already exists — leaving intact."
else
  echo "Creating Python package at ${PY_PKG_DIR} ..."
  mkdir -p "${PY_PKG_DIR}/cactus_eval_pkg"
  cat > "${PY_PKG_DIR}/cactus_eval_pkg/__init__.py" <<'PYINIT'
# Lightweight Python package to expose the compiled cactus_eval extension
try:
    # the compiled module will be named 'cactus_eval'
    from cactus_eval import *
except Exception as e:
    # If the extension hasn't been built/installed yet, provide a clear error
    raise ImportError("cactus_eval native extension not found. Build the C++ module with CMake (see setup script). Original error: " + str(e))
PYINIT

  # Minimal README and pyproject to allow local pip install if desired
  cat > "${PY_PKG_DIR}/README.md" <<'MD'
Python package wrapper for the cactus_eval extension.
Build the C++ extension (CMake) and place the resulting extension module next to this package,
or `pip install -e .` after creating an appropriate wheel.
MD

  cat > "${PY_PKG_DIR}/pyproject.toml" <<'PYPROJECT'
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"
PYPROJECT

  cat > "${PY_PKG_DIR}/setup.cfg" <<'SETUPCFG'
[metadata]
name = cactus_eval_pkg
version = 0.0.1
description = wrapper package for compiled cactus_eval extension
author = you
license = MIT
SETUPCFG

  cat > "${PY_PKG_DIR}/setup.py" <<'SETUPPY'
from setuptools import setup, find_packages
setup(
    name="cactus_eval_pkg",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,
)
SETUPPY

  echo "Created Python package skeleton."
fi

# 8) Build the C++ module via CMake
echo "Building C++ extension with CMake..."
mkdir -p "${BUILD_DIR}"
pushd "${BUILD_DIR}" >/dev/null

cmake -S "${SRC_DIR}" -B "${BUILD_DIR}" -DCMAKE_BUILD_TYPE=Release
cmake --build "${BUILD_DIR}" --config Release -- -j$(nproc 2>/dev/null || echo 2)

# After build, identify the produced .so (or .dylib) and copy it next to python package
echo "Locating compiled extension..."
EXT_SO="$(find "${BUILD_DIR}" -maxdepth 2 -type f -name "cactus_eval*.so" -print -quit || true)"
if [ -z "${EXT_SO}" ]; then
  # On macOS it can be .dylib or .so; try different patterns
  EXT_SO="$(find "${BUILD_DIR}" -maxdepth 2 -type f -name "cactus_eval*.dylib" -print -quit || true)"
fi

if [ -z "${EXT_SO}" ]; then
  echo "WARNING: Built extension not found automatically. Check ${BUILD_DIR} for *_cactus_eval*.so or similar file."
  popd >/dev/null
else
  echo "Found extension at: ${EXT_SO}"
  cp "${EXT_SO}" "${PY_PKG_DIR}/cactus_eval_pkg/"
  echo "Copied compiled extension into python package directory: ${PY_PKG_DIR}/cactus_eval_pkg/"
  popd >/dev/null
fi

# 9) Install the python package (editable) into the virtualenv
echo "Installing python wrapper package into virtualenv (editable mode)..."
pip install -U pip wheel setuptools
pip install -e "${PY_PKG_DIR}"

# 10) Quick smoke test
echo "Running quick smoke test (import and test evaluate_hand)..."
python - <<'PYTEST'
import sys
try:
    # import the extension via the package
    import cactus_eval
    print("Imported module 'cactus_eval' OK. evaluate_hand([1,2,3,4,5]) ->", cactus_eval.evaluate_hand([1,2,3,4,5]))
except Exception as e:
    print("Smoke test failed:", e)
    sys.exit(2)
PYTEST

echo "=== Setup complete ==="
echo "To use the virtualenv in your interactive shell, open a new shell in project directory (or run):"
echo "  cd ${PROJECT_DIR}"
echo "  pyenv activate ${VENV_NAME}"
echo "Alternatively, your shell may pick the virtualenv automatically because .python-version was written."
echo ""
echo "C++ source: ${SRC_DIR}"
echo "Build dir: ${BUILD_DIR}"
echo "Python package: ${PY_PKG_DIR}"
echo ""
echo "Notes:"
echo "- Replace the placeholder logic in ${SRC_DIR}/module.cpp with your full Cactus Kev evaluator implementation."
echo "- The pybind11 C++ API is already available (installed into this venv). Use pybind11 docs for examples of exposing C++ functions/classes to Python."
echo "- If you prefer a pure 'wheel' build of the extension, adapt CMake to produce a wheel or use setuptools-cmake / scikit-build. This script keeps it simple by copying the built extension next to the Python package."
