#!/usr/bin/env bash

# -----------------------------------------------------------------------------
# Poker Bot Evaluator Setup Script
# -----------------------------------------------------------------------------
# Creates a clean Python 3.12.0 virtual environment (via pyenv + venv)
# and builds the C++ evaluator module using CMake and pybind11.
# -----------------------------------------------------------------------------

# --- Detect and enter script directory ---
script_dir=$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd -P )
pushd "$script_dir" > /dev/null

echo "🔧 Setting up Poker Evaluator Environment..."

# --- Step 1: Install Python via pyenv (if not in Conda/Docker) ---
if [[ -z "$CONDA_DEFAULT_ENV" && ! -f /.dockerenv ]]; then
    echo "🧰 Checking Python installation via pyenv..."
    if ! command -v pyenv &> /dev/null; then
        echo "Installing pyenv..."
        curl -fsSL https://pyenv.run | bash
        export PYENV_ROOT="$HOME/.pyenv"
        export PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)"
    else
        eval "$(pyenv init -)"
    fi

    # Install Python 3.12.0 if not already installed
    pyenv install 3.12.0 --skip-existing
    pyenv versions
else
    echo "⚙️  Skipping pyenv setup (Conda or Docker environment detected)."
fi

# --- Step 2: Create virtual environment ---
echo "🐍 Creating virtual environment..."
python3 -m venv .venv

# --- Step 3: Activate virtual environment ---
source .venv/bin/activate
echo "✅ Virtual environment activated."

# --- Step 4: Upgrade pip and wheel ---
pip install --upgrade pip wheel setuptools

# --- Step 5: Install development & runtime dependencies ---
echo "📦 Installing Python dependencies..."
if [[ ! -f "requirements-dev.txt" ]]; then
    echo "Creating default requirements-dev.txt..."
    cat > requirements-dev.txt <<'REQS'
pybind11
cmake
REQS
fi
pip install -r requirements-dev.txt

# --- Step 6: Build the C++ evaluator via CMake ---
echo "⚙️  Building C++ evaluator module..."

mkdir -p cpp build
if [[ ! -f cpp/module.cpp ]]; then
    cat > cpp/module.cpp <<'CPP'
#include <pybind11/pybind11.h>
#include <vector>

namespace py = pybind11;

// Placeholder Cactus Kev evaluator stub
int evaluate_stub(const std::vector<int>& cards) {
    if (cards.size() < 5) return -1;
    int score = 0;
    for (int c : cards) score += c;
    return score;
}

PYBIND11_MODULE(cactus_eval, m) {
    m.doc() = "Cactus Kev style poker evaluator (C++/pybind11)";
    m.def("evaluate", &evaluate_stub, "Evaluate a 5+ card hand");
}
CPP
    echo "🧩 Created sample C++ evaluator source: cpp/module.cpp"
fi

cat > cpp/CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.12)
project(cactus_eval LANGUAGES CXX)

find_package(pybind11 REQUIRED)

pybind11_add_module(cactus_eval module.cpp)
target_compile_features(cactus_eval PRIVATE cxx_std_17)
CMAKE

# Build C++ extension
cmake -S cpp -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release

# Copy built module to Python package directory
mkdir -p poker_eval
cp build/*.so poker_eval/ 2>/dev/null || cp build/*.dylib poker_eval/ 2>/dev/null

# --- Step 7: Install the Python package itself ---
echo "📦 Installing local package in editable mode..."
cat > setup.py <<'SETUPPY'
from setuptools import setup, find_packages
setup(
    name="poker_eval",
    version="0.1.0",
    packages=find_packages(),
)
SETUPPY

pip install -e .

# --- Step 8: Quick test ---
echo "🧪 Running import test..."
python - <<'PYTEST'
try:
    import poker_eval.cactus_eval as ce
    print("✅ cactus_eval imported successfully.")
    print("Test result:", ce.evaluate([1,2,3,4,5]))
except Exception as e:
    print("❌ Import test failed:", e)
    exit(1)
PYTEST

echo "✅ Setup complete!"
echo "To activate this environment later, run:"
echo "  source .venv/bin/activate"

popd > /dev/null
