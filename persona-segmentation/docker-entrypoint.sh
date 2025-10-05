#!/bin/bash
set -e

# Docker entrypoint for Dutch Address Persona Segmentation
echo "=== Dutch Address Persona Segmentation ==="
echo "Container started at $(date)"

# Create output directory if it doesn't exist
mkdir -p /app/output

# Default addresses if none provided
DEFAULT_POSTCODE1="2051ER"
DEFAULT_POSTCODE2="2051NA"
DEFAULT_NUMBER1="2"
DEFAULT_NUMBER2="13-D"

# Parse command line arguments
if [ "$#" -eq 0 ]; then
    echo "Using default addresses: $DEFAULT_POSTCODE1 #$DEFAULT_NUMBER1 and $DEFAULT_POSTCODE2 #$DEFAULT_NUMBER2"
    exec Rscript /app/run_datasegmentation.R "$DEFAULT_POSTCODE1" "$DEFAULT_POSTCODE2" "$DEFAULT_NUMBER1" "$DEFAULT_NUMBER2"
elif [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo ""
    echo "Usage: docker run [options] datasegmentation [POSTCODE1] [POSTCODE2] [NUMBER1] [NUMBER2]"
    echo ""
    echo "Arguments:"
    echo "  POSTCODE1    First 6-digit Dutch postcode (e.g., 1011AB)"
    echo "  POSTCODE2    Second 6-digit Dutch postcode (e.g., 2051ER)"
    echo "  NUMBER1      First house number (e.g., 12, 5A, 123-C)"
    echo "  NUMBER2      Second house number (e.g., 5, 25B, 10-D)"
    echo ""
    echo "Examples:"
    echo "  # Use default addresses"
    echo "  docker run --rm -v \$(pwd)/output:/app/output datasegmentation"
    echo ""
    echo "  # Custom addresses"
    echo "  docker run --rm -v \$(pwd)/output:/app/output datasegmentation 1011AB 2051ER 12 5A"
    echo ""
    echo "  # Rural vs urban comparison"
    echo "  docker run --rm -v \$(pwd)/output:/app/output datasegmentation 7411AA 1012JS 8 156"
    echo ""
    echo "Output will be saved to ./output/user_predictions.csv"
    echo ""
    exit 0
elif [ "$1" = "test" ]; then
    echo "Running container health check..."
    echo "R version: $(R --version | head -1)"
    echo "Python version: $(python3 --version)"
    echo "Required R packages:"
    Rscript -e "packages <- c('dplyr', 'ranger', 'caret', 'readxl'); sapply(packages, function(p) cat(sprintf('  %s: %s\n', p, packageVersion(p))))"
    echo "Data files:"
    ls -la /app/*.csv /app/*.xls 2>/dev/null || echo "  Training data files not found"
    ls -la /app/cbs_postcode_data/ 2>/dev/null || echo "  CBS data not downloaded"
    echo "Container test completed successfully"
    exit 0
elif [ "$1" = "bash" ] || [ "$1" = "shell" ]; then
    echo "Starting interactive bash shell..."
    exec /bin/bash
elif [ "$1" = "Rscript" ]; then
    # Pass through Rscript commands
    exec "$@"
elif [ "$#" -eq 1 ]; then
    echo "Error: Please provide both postcodes and house numbers, or use 'help' for usage information"
    exit 1
elif [ "$#" -eq 2 ]; then
    echo "Using provided postcodes with default house numbers"
    exec Rscript /app/run_datasegmentation.R "$1" "$2" "$DEFAULT_NUMBER1" "$DEFAULT_NUMBER2"
elif [ "$#" -eq 4 ]; then
    echo "Using provided postcodes: $1 #$3 and $2 #$4"
    exec Rscript /app/run_datasegmentation.R "$1" "$2" "$3" "$4"
else
    echo "Error: Invalid number of arguments. Use 'help' for usage information"
    exit 1
fi