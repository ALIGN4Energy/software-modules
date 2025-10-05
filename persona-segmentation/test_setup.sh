#!/bin/bash

echo "=== TESTING DATASEGMENTATION SETUP ==="

# Check if required files exist
echo "Checking required files..."

# Check confidential data files
echo ""
echo "Checking confidential data files..."
confidential_files=(
    "confidential_data/output.csv"
    "confidential_data/data_long_4c.xls"
    "confidential_data/150911-Gemiddeld-besteedbaar-huishoudinkomen-per-postcode-mw.xls"
)

missing_confidential=()

for file in "${confidential_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_confidential+=("$file")
    else
        echo "✓ $file exists"
    fi
done

if [ ${#missing_confidential[@]} -gt 0 ]; then
    echo "❌ Missing confidential data files:"
    printf '   %s\n' "${missing_confidential[@]}"
    echo ""
    echo "These files are required but not in the repository."
    echo "Please ensure you have access to the LISS panel data."
    exit 1
fi

# Check code files
echo ""
echo "Checking code files..."
code_files=(
    "download_netherlands_data.py"
    "Dockerfile"
    "run_datasegmentation_main.R"
    "docker-entrypoint.sh"
)

missing_code=()

for file in "${code_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_code+=("$file")
    else
        echo "✓ $file exists"
    fi
done

if [ ${#missing_code[@]} -gt 0 ]; then
    echo "❌ Missing code files:"
    printf '   %s\n' "${missing_code[@]}"
    exit 1
fi

echo ""
echo "✓ All required files present"

# Test data download script
echo ""
echo "Testing data download..."
python3 download_netherlands_data.py

if [ $? -eq 0 ]; then
    echo "✓ Data download successful"
else
    echo "❌ Data download failed"
    exit 1
fi

# Check if CBS data was downloaded
if [ -d "cbs_postcode_data" ] && [ -f "cbs_postcode_data/bag_data.csv" ]; then
    echo "✓ CBS and BAG data downloaded"
    echo "   Files in cbs_postcode_data/:"
    ls -la cbs_postcode_data/
else
    echo "❌ CBS/BAG data not found"
    exit 1
fi

echo ""
echo "=== SETUP TEST COMPLETED SUCCESSFULLY ==="
echo ""
echo "Next steps:"
echo "1. Start Docker Desktop"
echo "2. Run: docker build -t datasegmentation ."
echo "3. Run: docker run --rm -v \$(pwd)/output:/app/output datasegmentation"
echo ""
echo "Usage examples:"
echo "# Default addresses:"
echo "docker run --rm -v \$(pwd)/output:/app/output datasegmentation"
echo ""
echo "# Custom addresses:"
echo "docker run --rm -v \$(pwd)/output:/app/output datasegmentation \"1011AB\" \"2051ER\" \"12\" \"5A\""
echo ""
echo "# Get help:"
echo "docker run --rm datasegmentation help"
echo ""
echo "# Test container:"
echo "docker run --rm datasegmentation test"