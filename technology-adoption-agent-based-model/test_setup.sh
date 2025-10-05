#!/bin/bash

echo "=== TESTING ABM SETUP ==="

# Check if required files exist
echo "Checking required files..."

required_files=(
    "ABM.py"
    "run_abm.py"
    "tutorial_households.csv"
    "tutorial_technologies.csv"
    "Dockerfile"
    "docker-entrypoint.sh"
)

missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    else
        echo "✓ $file exists"
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "❌ Missing required files:"
    printf '   %s\n' "${missing_files[@]}"
    exit 1
fi

echo ""
echo "✓ All required files present"

# Test Python dependencies
echo ""
echo "Testing Python dependencies..."

python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠ Warning: Python 3.11+ recommended (you have $(python3 --version))"
else
    echo "✓ Python version: $(python3 --version)"
fi

# Check for required packages
packages=("numpy" "pandas" "mesa")
missing_packages=()

for pkg in "${packages[@]}"; do
    python3 -c "import $pkg" 2>/dev/null
    if [ $? -eq 0 ]; then
        version=$(python3 -c "import $pkg; print($pkg.__version__)")
        echo "✓ $pkg $version"
    else
        missing_packages+=("$pkg")
        echo "❌ $pkg not installed"
    fi
done

if [ ${#missing_packages[@]} -gt 0 ]; then
    echo ""
    echo "❌ Missing Python packages. Install with:"
    echo "   pip install ${missing_packages[*]}"
    echo ""
    echo "Or use Docker (recommended):"
    echo "   docker build -t abm ."
    exit 1
fi

# Validate CSV files
echo ""
echo "Validating data files..."

# Check tutorial_households.csv
if ! python3 -c "import pandas as pd; df = pd.read_csv('tutorial_households.csv'); assert 'Agent_id' in df.columns" 2>/dev/null; then
    echo "❌ tutorial_households.csv is invalid or missing required columns"
    exit 1
else
    n_households=$(python3 -c "import pandas as pd; print(len(pd.read_csv('tutorial_households.csv')))")
    echo "✓ tutorial_households.csv valid ($n_households households)"
fi

# Check tutorial_technologies.csv
if ! python3 -c "import pandas as pd; df = pd.read_csv('tutorial_technologies.csv'); assert 'technology' in df.columns" 2>/dev/null; then
    echo "❌ tutorial_technologies.csv is invalid or missing required columns"
    exit 1
else
    n_techs=$(python3 -c "import pandas as pd; print(len(pd.read_csv('tutorial_technologies.csv')))")
    techs=$(python3 -c "import pandas as pd; print(', '.join(pd.read_csv('tutorial_technologies.csv')['technology'].tolist()))")
    echo "✓ tutorial_technologies.csv valid ($n_techs technologies: $techs)"
fi

# Test ABM import
echo ""
echo "Testing ABM import..."
python3 -c "from ABM import HeatingModel, Household, run_monte_carlo_simulation; print('✓ ABM imports successfully')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ ABM.py has import errors"
    python3 -c "from ABM import HeatingModel, Household, run_monte_carlo_simulation"
    exit 1
fi

# Test run_abm.py
echo ""
echo "Testing run_abm.py..."
python3 run_abm.py --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ run_abm.py --help works"
else
    echo "❌ run_abm.py has errors"
    exit 1
fi

echo ""
echo "=== SETUP TEST COMPLETED SUCCESSFULLY ==="
echo ""
echo "Next steps:"
echo ""
echo "Option 1: Run locally with Python"
echo "  python run_abm.py"
echo "  python run_abm.py --n_runs 50 --years 15"
echo "  python run_abm.py --help"
echo ""
echo "Option 2: Run with Docker (recommended)"
echo "  1. Start Docker Desktop"
echo "  2. docker build -t abm ."
echo "  3. docker run --rm -v \$(pwd)/output:/app/output abm"
echo ""
echo "Usage examples:"
echo "  # Default (100 runs, 10 years, policy=true, peer_effect=0.2)"
echo "  docker run --rm -v \$(pwd)/output:/app/output abm"
echo ""
echo "  # Custom parameters"
echo "  docker run --rm -v \$(pwd)/output:/app/output abm --n_runs 50 --years 15"
echo ""
echo "  # No policy support"
echo "  docker run --rm -v \$(pwd)/output:/app/output abm --policy false"
echo ""
echo "  # Strong peer effects"
echo "  docker run --rm -v \$(pwd)/output:/app/output abm --peer_effect 0.5"
echo ""
echo "  # Get help"
echo "  docker run --rm abm help"
