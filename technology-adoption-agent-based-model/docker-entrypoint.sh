#!/bin/bash
set -e

# Docker entrypoint for Energy Technology Adoption ABM
echo "=== Energy Technology Adoption Agent-Based Model ==="
echo "Container started at $(date)"

# Create output directory if it doesn't exist
mkdir -p /app/output

# Parse command line arguments
if [ "$#" -eq 0 ]; then
    echo "Error: Missing required arguments"
    echo ""
    echo "You must specify household data and technology config files:"
    echo "  --household_data PATH"
    echo "  --tech_config PATH"
    echo ""
    echo "Run 'docker run --rm technology-adoption-abm help' for usage examples"
    exit 1
elif [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo ""
    echo "Usage: docker run [options] abm [COMMAND|OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  help              Show this help message"
    echo "  test              Run container health check"
    echo "  bash/shell        Start interactive bash shell"
    echo ""
    echo "Required Options:"
    echo "  --household_data PATH   Path to household data CSV (required)"
    echo "  --tech_config PATH      Path to technology config CSV (required)"
    echo ""
    echo "Optional Parameters:"
    echo "  --n_runs N              Number of Monte Carlo runs (default: 100)"
    echo "  --years Y               Simulation years per run (default: 10)"
    echo "  --policy true/false     Enable/disable policy support (default: true)"
    echo "  --peer_effect P         Peer effect strength 0-1 (default: 0.2)"
    echo "  --output_dir PATH       Output directory (default: output)"
    echo ""
    echo "Examples:"
    echo "  # Basic run with tutorial data"
    echo "  docker run --rm -v \$(pwd):/app technology-adoption-abm \\"
    echo "    --household_data tutorial_households.csv \\"
    echo "    --tech_config tutorial_technologies.csv"
    echo ""
    echo "  # Custom Monte Carlo runs and years"
    echo "  docker run --rm -v \$(pwd):/app technology-adoption-abm \\"
    echo "    --household_data tutorial_households.csv \\"
    echo "    --tech_config tutorial_technologies.csv \\"
    echo "    --n_runs 50 --years 15"
    echo ""
    echo "  # No policy support scenario"
    echo "  docker run --rm -v \$(pwd):/app technology-adoption-abm \\"
    echo "    --household_data tutorial_households.csv \\"
    echo "    --tech_config tutorial_technologies.csv \\"
    echo "    --policy false"
    echo ""
    echo "  # Custom data files"
    echo "  docker run --rm -v \$(pwd):/app technology-adoption-abm \\"
    echo "    --household_data my_households.csv \\"
    echo "    --tech_config my_technologies.csv \\"
    echo "    --n_runs 200 --years 20 --peer_effect 0.3"
    echo ""
    echo "Output Files:"
    echo "  ./output/monte_carlo_results.csv   - Detailed results per run"
    echo "  ./output/summary_statistics.txt    - Mean adoption rates and statistics"
    echo ""
    echo "Note: Mount your data directory with -v \$(pwd):/app to access local CSV files"
    echo ""
    exit 0
elif [ "$1" = "test" ]; then
    echo "Running container health check..."
    echo "Python version: $(python3 --version)"
    echo "Required Python packages:"
    python3 -c "import numpy; print(f'  numpy: {numpy.__version__}')"
    python3 -c "import pandas; print(f'  pandas: {pandas.__version__}')"
    python3 -c "import mesa; print(f'  mesa: {mesa.__version__}')"
    echo "Data files:"
    ls -la /app/*.csv 2>/dev/null || echo "  Data files not found"
    ls -la /app/ABM.py 2>/dev/null || echo "  ABM.py not found"
    echo "Container test completed successfully"
    exit 0
elif [ "$1" = "bash" ] || [ "$1" = "shell" ]; then
    echo "Starting interactive bash shell..."
    exec /bin/bash
elif [ "$1" = "python" ] || [ "$1" = "python3" ]; then
    # Pass through Python commands
    exec "$@"
else
    # Parse custom arguments
    exec python3 /app/run_abm.py "$@"
fi
