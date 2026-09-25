#!/bin/bash

echo "=== TESTING PERSONA SEGMENTATION SETUP ==="

# Check code, model and example files
echo ""
echo "Checking required files..."
required_files=(
    "persona_assignment.Rmd"
    "models/persona_rf.rds"
    "examples/addresses_example.csv"
    "download_netherlands_data.py"
    "Dockerfile"
    "docker-entrypoint.sh"
)

missing=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing+=("$file")
    else
        echo "✓ $file exists"
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    echo "❌ Missing files:"
    printf '   %s\n' "${missing[@]}"
    exit 1
fi

# Check that Docker is available
echo ""
echo "Checking Docker..."
if docker info > /dev/null 2>&1; then
    echo "✓ Docker is running"
else
    echo "❌ Docker is not running"
    exit 1
fi

echo ""
echo "=== SETUP TEST COMPLETED SUCCESSFULLY ==="
echo ""
echo "Next steps:"
echo "1. Build:            docker build -t persona-segmentation ."
echo "2. Download data:    docker run --rm -v persona-data:/data persona-segmentation download"
echo "3. Predict:          docker run --rm -v persona-data:/data -v \$(pwd)/output:/app/output persona-segmentation 1011AB 12"
echo ""
echo "Help:                docker run --rm persona-segmentation help"
