#!/bin/bash

# Comprehensive Docker test script for profile-generator

set -e

echo "==================================================================="
echo "      PROFILE-GENERATOR DOCKER COMPREHENSIVE TEST"
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

# Build the Docker image
echo "Step 2: Building Docker image..."
echo "This may take a few minutes..."
echo ""

BUILD_START=$(date +%s)
if docker build -t profile-generator . ; then
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
echo "Step 3: Verifying Docker image..."
if docker images | grep -q profile-generator; then
    IMAGE_SIZE=$(docker images profile-generator --format "{{.Size}}")
    echo -e "${GREEN}✓ Image exists (size: ${IMAGE_SIZE})${NC}"
else
    echo -e "${RED}✗ Image not found${NC}"
    exit 1
fi

# Test 1: Help command
echo ""
echo "==================================================================="
echo "TEST 1: Help command"
echo "==================================================================="
echo "Command: docker run --rm profile-generator help"
echo ""
if docker run --rm profile-generator help > /tmp/pg_help.txt 2>&1; then
    if grep -q "Usage:" /tmp/pg_help.txt; then
        echo -e "${GREEN}✓ Help command works${NC}"
        echo ""
        echo "Help output preview:"
        head -15 /tmp/pg_help.txt
    else
        echo -e "${RED}✗ Help output doesn't contain expected content${NC}"
    fi
else
    echo -e "${RED}✗ Help command failed${NC}"
fi

# Test 2: Demo command
echo ""
echo "==================================================================="
echo "TEST 2: Demo data generation"
echo "==================================================================="
echo "Command: docker run --rm profile-generator demo"
echo ""
if docker run --rm profile-generator demo > /tmp/pg_demo.txt 2>&1; then
    echo -e "${GREEN}✓ Demo generation completed${NC}"
    echo ""
    echo "Demo output:"
    cat /tmp/pg_demo.txt

    # Validate output
    if grep -q "Generated data shape: (5, 96)" /tmp/pg_demo.txt; then
        echo ""
        echo -e "${GREEN}✓ Output format is correct${NC}"
    else
        echo -e "${YELLOW}⚠ Unexpected output format${NC}"
    fi
else
    echo -e "${RED}✗ Demo generation failed${NC}"
    cat /tmp/pg_demo.txt
fi

# Test 3: Default command (should run demo)
echo ""
echo "==================================================================="
echo "TEST 3: Default command (no arguments)"
echo "==================================================================="
echo "Command: docker run --rm profile-generator"
echo ""
if docker run --rm profile-generator > /tmp/pg_default.txt 2>&1; then
    echo -e "${GREEN}✓ Default command completed${NC}"

    if grep -q "Generated data shape" /tmp/pg_default.txt; then
        echo -e "${GREEN}✓ Default runs demo as expected${NC}"
    else
        echo -e "${RED}✗ Default command doesn't run demo${NC}"
    fi
else
    echo -e "${RED}✗ Default command failed${NC}"
fi

# Test 4: Test suite
echo ""
echo "==================================================================="
echo "TEST 4: Test suite"
echo "==================================================================="
echo "Command: docker run --rm profile-generator test"
echo ""
if docker run --rm profile-generator test > /tmp/pg_test.txt 2>&1; then
    echo -e "${GREEN}✓ Tests completed${NC}"
    echo ""
    echo "Test output:"
    cat /tmp/pg_test.txt

    # Check if all tests passed
    if grep -q "5 passed" /tmp/pg_test.txt; then
        echo ""
        echo -e "${GREEN}✓ All tests passed${NC}"
    else
        echo -e "${RED}✗ Some tests failed${NC}"
    fi
else
    echo -e "${RED}✗ Test suite failed${NC}"
    cat /tmp/pg_test.txt
fi

# Test 5: Custom Python script
echo ""
echo "==================================================================="
echo "TEST 5: Custom Python script execution"
echo "==================================================================="

# Create a test script
cat > /tmp/test_custom.py << 'EOF'
from profile_generator.interfaces.demo_model.config import (
    DemoModelConfig, DemoSampleConfig, DemoSampleCondition, Month
)
from profile_generator.interfaces.demo_model.model import DemoModel

# Generate profiles for different months
model = DemoModel(DemoModelConfig(model_path='tests/models/demo_model_state_dict.pt'))

for month in [Month.JANUARY, Month.JULY]:
    profiles = model.sample(
        DemoSampleConfig(batch_size=3),
        DemoSampleCondition(month=month, annual_consumption=6000.0)
    )
    print(f"{month.name}: avg={profiles.mean():.2f}, shape={tuple(profiles.shape)}")
EOF

echo "Command: docker run --rm -v /tmp/test_custom.py:/app/test_custom.py profile-generator python test_custom.py"
echo ""
if docker run --rm -v /tmp/test_custom.py:/app/test_custom.py profile-generator python test_custom.py > /tmp/pg_custom.txt 2>&1; then
    echo -e "${GREEN}✓ Custom script executed${NC}"
    echo ""
    echo "Custom script output:"
    cat /tmp/pg_custom.txt
else
    echo -e "${RED}✗ Custom script failed${NC}"
    cat /tmp/pg_custom.txt
fi

# Test 6: Interactive shell test (non-interactive)
echo ""
echo "==================================================================="
echo "TEST 6: Python import test"
echo "==================================================================="
echo "Command: docker run --rm profile-generator python -c \"import profile_generator; print('✓ Imports work')\""
echo ""
if docker run --rm profile-generator python -c "import profile_generator; print('✓ Imports work')" > /tmp/pg_import.txt 2>&1; then
    echo -e "${GREEN}✓ Python imports work${NC}"
    cat /tmp/pg_import.txt
else
    echo -e "${RED}✗ Python imports failed${NC}"
    cat /tmp/pg_import.txt
fi

# Summary
echo ""
echo "==================================================================="
echo "                        TEST SUMMARY"
echo "==================================================================="
echo ""
echo "All Docker commands have been tested."
echo ""
echo "Quick reference commands:"
echo "  docker run --rm profile-generator                    # Run demo"
echo "  docker run --rm profile-generator test              # Run tests"
echo "  docker run --rm profile-generator help              # Show help"
echo "  docker run --rm -it profile-generator shell         # Python shell"
echo "  docker run --rm -it profile-generator bash          # Bash shell"
echo ""
echo -e "${GREEN}✓ Testing complete!${NC}"
echo ""

# Cleanup
rm -f /tmp/pg_*.txt /tmp/test_custom.py
