#!/bin/bash
set -e

echo "=== Energy Consumption Profile Generator (EnergyDiff) ==="
echo "Container started at $(date)"
echo ""

# Handle different commands
case "$1" in
    help|--help|-h)
        echo "Usage: docker run [options] profile-generator [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  generate          Generate annual energy consumption profiles using EnergyDiff (CLI)"
        echo "  demo              Run demo data generation (uses simple demo model)"
        echo "  test              Run test suite"
        echo "  shell             Start interactive Python shell"
        echo "  bash              Start bash shell"
        echo "  python [args]     Run Python with arguments"
        echo "  help              Show this help message"
        echo ""
        echo "Examples:"
        echo "  # Generate profile using EnergyDiff model"
        echo "  docker run --rm \\"
        echo "    -v \$(pwd)/models:/app/models \\"
        echo "    -v \$(pwd)/output:/app/output \\"
        echo "    profile-generator generate \\"
        echo "    --model_path /app/models/energydiff-2025-12-22.ckpt \\"
        echo "    --annual_consumption 7500 \\"
        echo "    --output output/profile.json"
        echo ""
        echo "  # Generate profile with all technologies"
        echo "  docker run --rm \\"
        echo "    -v \$(pwd)/models:/app/models \\"
        echo "    -v \$(pwd)/output:/app/output \\"
        echo "    profile-generator generate \\"
        echo "    --model_path /app/models/energydiff-2025-12-22.ckpt \\"
        echo "    --annual_consumption 9000 \\"
        echo "    --has_heatpump true \\"
        echo "    --has_solar true \\"
        echo "    --has_ev true \\"
        echo "    --num_steps 200 \\"
        echo "    --output output/profile.json"
        echo ""
        echo "  # Run demo (simple model)"
        echo "  docker run --rm profile-generator demo"
        echo ""
        echo "  # Run tests"
        echo "  docker run --rm profile-generator test"
        echo ""
        echo "  # Get help for generate command"
        echo "  docker run --rm profile-generator generate --help"
        echo ""
        exit 0
        ;;

    generate)
        shift
        echo "Generating annual energy consumption profiles using EnergyDiff..."
        echo ""
        exec python scripts/generate_profile_cli.py "$@"
        ;;

    test)
        echo "Running test suite..."
        echo ""
        exec pytest tests/ -v
        ;;

    demo)
        echo "Running demo data generation..."
        echo ""
        exec python scripts/generate_demo_data.py
        ;;

    shell)
        echo "Starting interactive Python shell..."
        echo "Import example: from profile_generator.interfaces.energydiff.model import EnergyDiffModel"
        echo ""
        exec python
        ;;

    bash)
        echo "Starting bash shell..."
        exec /bin/bash
        ;;

    python)
        shift
        exec python "$@"
        ;;

    *)
        if [ -z "$1" ]; then
            # No arguments, run demo
            echo "Running demo data generation..."
            echo ""
            exec python scripts/generate_demo_data.py
        else
            # Unknown command
            echo "Unknown command: $1"
            echo "Run 'docker run --rm profile-generator help' for usage information"
            exit 1
        fi
        ;;
esac
