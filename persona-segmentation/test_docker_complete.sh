#!/bin/bash

# Builds the image and runs every documented command.
# The first run downloads about 8 GB of open data into the Docker volume "persona-data".

set -e

IMAGE=persona-segmentation
VOLUME=persona-data
OUTPUT="$(pwd)/output"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

pass() { echo -e "${GREEN}✓ $1${NC}"; }
fail() { echo -e "${RED}✗ $1${NC}"; exit 1; }

run() {
    docker run --rm -v "$VOLUME":/data -v "$OUTPUT":/app/output "$IMAGE" "$@"
}

# Checks that the output has one row per address and a persona in every row
check_output() {
    local expected=$1
    local csv="$OUTPUT/persona_predictions.csv"
    [ -f "$csv" ] || fail "no output file"
    head -1 "$csv" | grep -q "persona_label" || fail "output has no persona_label column"
    local rows
    rows=$(python3 -c "import csv,sys; r=list(csv.DictReader(open(sys.argv[1]))); print(sum(1 for x in r if x['persona_label']))" "$csv")
    [ "$rows" -eq "$expected" ] || fail "expected $expected predictions, got $rows"
    pass "$rows predictions"
}

echo "=== PERSONA-SEGMENTATION DOCKER TEST ==="

docker info > /dev/null 2>&1 || fail "Docker is not running"
pass "Docker is running"

echo ""
echo "Building image..."
docker build -t "$IMAGE" . || fail "build failed"
pass "image built"

mkdir -p "$OUTPUT"

echo ""
echo "TEST 1: help"
docker run --rm "$IMAGE" help | grep -q "Usage:" || fail "help output"
pass "help works"

echo ""
echo "TEST 2: download (skips files that are already present)"
run download || fail "download failed"
pass "open data present"

echo ""
echo "TEST 3: test command"
run test || fail "test command failed"
pass "test command works"

echo ""
echo "TEST 4: example addresses"
rm -f "$OUTPUT/persona_predictions.csv"
run || fail "prediction failed"
check_output "$(($(wc -l < examples/addresses_example.csv) - 1))"

echo ""
echo "TEST 5: postcode + house number pairs"
rm -f "$OUTPUT/persona_predictions.csv"
run 2051ER 2 2051NA 13-D || fail "prediction failed"
check_output 2

echo ""
echo "TEST 6: address file"
rm -f "$OUTPUT/persona_predictions.csv"
docker run --rm -v "$VOLUME":/data -v "$OUTPUT":/app/output \
    -v "$(pwd)/examples/addresses_example.csv":/app/input.csv "$IMAGE" /app/input.csv || fail "prediction failed"
check_output "$(($(wc -l < examples/addresses_example.csv) - 1))"

echo ""
echo "TEST 7: odd number of arguments is rejected"
if run 2051ER > /dev/null 2>&1; then fail "odd argument count was accepted"; fi
pass "odd argument count rejected"

echo ""
pass "all tests passed"
