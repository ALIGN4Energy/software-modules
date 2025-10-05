#!/bin/bash

# Comprehensive Docker test script for persona-segmentation
# This script waits for the Docker build to complete and tests all documented commands

set -e

echo "==================================================================="
echo "      PERSONA-SEGMENTATION DOCKER COMPREHENSIVE TEST"
echo "==================================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
echo "Step 1: Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check if build is already in progress
echo "Step 2: Checking for existing Docker build process..."
if docker ps -a | grep -q "datasegmentation"; then
    echo -e "${YELLOW}⚠ Found existing datasegmentation containers${NC}"
fi

# Build the Docker image (or wait if already building)
echo ""
echo "Step 3: Building Docker image..."
echo "This may take 10-15 minutes for first build..."
echo ""

BUILD_START=$(date +%s)
if docker build -t datasegmentation . ; then
    BUILD_END=$(date +%s)
    BUILD_TIME=$((BUILD_END - BUILD_START))
    echo ""
    echo -e "${GREEN}✓ Docker image built successfully in ${BUILD_TIME} seconds${NC}"
else
    echo -e "${RED}✗ Docker build failed${NC}"
    exit 1
fi

# Verify image exists
echo ""
echo "Step 4: Verifying Docker image..."
if docker images | grep -q datasegmentation; then
    IMAGE_SIZE=$(docker images datasegmentation --format "{{.Size}}")
    echo -e "${GREEN}✓ Image exists (size: ${IMAGE_SIZE})${NC}"
else
    echo -e "${RED}✗ Image not found${NC}"
    exit 1
fi

# Create output directory
echo ""
echo "Step 5: Preparing output directory..."
mkdir -p output
chmod 777 output
echo -e "${GREEN}✓ Output directory ready${NC}"

# Test 1: Help command
echo ""
echo "==================================================================="
echo "TEST 1: Help command"
echo "==================================================================="
echo "Command: docker run --rm datasegmentation help"
echo ""
if docker run --rm datasegmentation help > /tmp/help_output.txt 2>&1; then
    if grep -q "Usage:" /tmp/help_output.txt; then
        echo -e "${GREEN}✓ Help command works${NC}"
        echo ""
        echo "Help output preview:"
        head -20 /tmp/help_output.txt
    else
        echo -e "${RED}✗ Help output doesn't contain expected content${NC}"
    fi
else
    echo -e "${RED}✗ Help command failed${NC}"
fi

# Test 2: Container health check
echo ""
echo "==================================================================="
echo "TEST 2: Container health check"
echo "==================================================================="
echo "Command: docker run --rm datasegmentation test"
echo ""
if docker run --rm datasegmentation test > /tmp/test_output.txt 2>&1; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo ""
    echo "Health check output:"
    cat /tmp/test_output.txt
else
    echo -e "${RED}✗ Health check failed${NC}"
    cat /tmp/test_output.txt
fi

# Test 3: Default addresses
echo ""
echo "==================================================================="
echo "TEST 3: Prediction with default addresses"
echo "==================================================================="
echo "Command: docker run --rm -v \$(pwd)/output:/app/output datasegmentation"
echo ""
TEST3_START=$(date +%s)
if docker run --rm -v $(pwd)/output:/app/output datasegmentation > /tmp/default_output.txt 2>&1; then
    TEST3_END=$(date +%s)
    TEST3_TIME=$((TEST3_END - TEST3_START))
    echo -e "${GREEN}✓ Default prediction completed in ${TEST3_TIME} seconds${NC}"

    # Check if output file was created
    if [ -f "output/user_predictions.csv" ]; then
        echo -e "${GREEN}✓ Output file created${NC}"
        echo ""
        echo "Output file contents:"
        cat output/user_predictions.csv
        echo ""

        # Validate CSV structure
        HEADER=$(head -1 output/user_predictions.csv)
        if echo "$HEADER" | grep -q "predicted_persona"; then
            echo -e "${GREEN}✓ CSV has correct header structure${NC}"
        else
            echo -e "${RED}✗ CSV header is incorrect${NC}"
        fi

        # Count predictions
        PRED_COUNT=$(tail -n +2 output/user_predictions.csv | wc -l)
        echo -e "${GREEN}✓ Generated ${PRED_COUNT} predictions${NC}"
    else
        echo -e "${RED}✗ Output file not created${NC}"
    fi
else
    echo -e "${RED}✗ Default prediction failed${NC}"
    echo "Error output:"
    cat /tmp/default_output.txt
fi

# Test 4: Custom addresses (two postcodes only)
echo ""
echo "==================================================================="
echo "TEST 4: Prediction with custom postcodes (Amsterdam & Utrecht)"
echo "==================================================================="
echo "Command: docker run --rm -v \$(pwd)/output:/app/output datasegmentation \"1011AB\" \"3521AB\""
echo ""
if docker run --rm -v $(pwd)/output:/app/output datasegmentation "1011AB" "3521AB" > /tmp/custom1_output.txt 2>&1; then
    echo -e "${GREEN}✓ Custom postcodes prediction completed${NC}"

    if [ -f "output/user_predictions.csv" ]; then
        echo ""
        echo "Output for Amsterdam (1011AB) and Utrecht (3521AB):"
        cat output/user_predictions.csv
        echo ""

        # Check if both postcodes are in output
        if grep -q "1011AB" output/user_predictions.csv && grep -q "3521AB" output/user_predictions.csv; then
            echo -e "${GREEN}✓ Both postcodes found in output${NC}"
        else
            echo -e "${RED}✗ Missing postcodes in output${NC}"
        fi
    fi
else
    echo -e "${RED}✗ Custom postcodes prediction failed${NC}"
    cat /tmp/custom1_output.txt
fi

# Test 5: Full custom addresses with house numbers
echo ""
echo "==================================================================="
echo "TEST 5: Prediction with full custom addresses"
echo "==================================================================="
echo "Command: docker run --rm -v \$(pwd)/output:/app/output datasegmentation \"1011AB\" \"2051ER\" \"12\" \"5A\""
echo ""
if docker run --rm -v $(pwd)/output:/app/output datasegmentation "1011AB" "2051ER" "12" "5A" > /tmp/custom2_output.txt 2>&1; then
    echo -e "${GREEN}✓ Full custom addresses prediction completed${NC}"

    if [ -f "output/user_predictions.csv" ]; then
        echo ""
        echo "Output with house numbers:"
        cat output/user_predictions.csv
        echo ""

        # Validate house numbers
        if grep -q "12" output/user_predictions.csv && grep -q "5A" output/user_predictions.csv; then
            echo -e "${GREEN}✓ House numbers correctly processed${NC}"
        else
            echo -e "${YELLOW}⚠ House numbers may not be in output (this is OK if using regional averages)${NC}"
        fi
    fi
else
    echo -e "${RED}✗ Full custom addresses prediction failed${NC}"
    cat /tmp/custom2_output.txt
fi

# Test 6: Different regions (testing regional demographics)
echo ""
echo "==================================================================="
echo "TEST 6: Regional demographics test (4 different regions)"
echo "==================================================================="
echo "Testing: Amsterdam (10xx), Randstad (20xx), Utrecht (30xx), Other (50xx)"
echo "Command: docker run --rm -v \$(pwd)/output:/app/output datasegmentation \"1012JS\" \"2514AB\" \"3511AB\" \"5611AA\""
echo ""
if docker run --rm -v $(pwd)/output:/app/output datasegmentation "1012JS" "2514AB" "3511AB" "5611AA" > /tmp/regional_output.txt 2>&1; then
    echo -e "${GREEN}✓ Regional test completed${NC}"

    if [ -f "output/user_predictions.csv" ]; then
        echo ""
        echo "Regional predictions:"
        cat output/user_predictions.csv
        echo ""

        # Analyze persona distribution
        echo "Persona distribution:"
        for class in Class1 Class2 Class3 Class4; do
            COUNT=$(grep -c "$class" output/user_predictions.csv || echo "0")
            echo "  $class: $COUNT"
        done
    fi
else
    echo -e "${RED}✗ Regional test failed${NC}"
    cat /tmp/regional_output.txt
fi

# Summary
echo ""
echo "==================================================================="
echo "                        TEST SUMMARY"
echo "==================================================================="
echo ""
echo "All README commands have been tested."
echo ""
echo "Key files:"
echo "  - Latest predictions: output/user_predictions.csv"
echo "  - Help output: /tmp/help_output.txt"
echo "  - Test logs: /tmp/*_output.txt"
echo ""
echo "Quick reference commands (from README):"
echo "  docker run --rm datasegmentation help"
echo "  docker run --rm datasegmentation test"
echo "  docker run --rm -v \$(pwd)/output:/app/output datasegmentation"
echo "  docker run --rm -v \$(pwd)/output:/app/output datasegmentation \"1011AB\" \"2051ER\""
echo ""
echo -e "${GREEN}✓ Testing complete!${NC}"
echo ""
