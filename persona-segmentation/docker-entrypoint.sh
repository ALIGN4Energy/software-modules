#!/bin/bash
set -e

# Docker entrypoint for Dutch Address Persona Segmentation
echo "=== Dutch Address Persona Segmentation ==="

CBS_YEAR="${PERSONA_CBS_YEAR:-2025}"
INCOME_YEAR="${PERSONA_INCOME_YEAR:-2023}"

usage() {
    cat <<EOF

Usage: docker run [options] persona-segmentation COMMAND

Commands:
  download                    Download CBS and BAG open data into /data (once, about 8 GB)
  (no command)                Predict personas for examples/addresses_example.csv
  POSTCODE NUMBER [...]       Predict personas for one or more postcode + house number pairs
  FILE.csv | FILE.xlsx        Predict personas for an address file (path inside the container)
  test                        Check the R packages, the model and the open data
  help                        Show this message
  bash                        Start a shell

Mount a folder on /data for the open data and a folder on /app/output for the results.

Examples:
  docker run --rm -v persona-data:/data persona-segmentation download
  docker run --rm -v persona-data:/data -v \$(pwd)/output:/app/output persona-segmentation
  docker run --rm -v persona-data:/data -v \$(pwd)/output:/app/output persona-segmentation 1011AB 12 2514JG 20
  docker run --rm -v persona-data:/data -v \$(pwd)/output:/app/output -v \$(pwd)/addresses.csv:/app/input.csv persona-segmentation /app/input.csv

Environment: PERSONA_CBS_YEAR (default 2025), PERSONA_INCOME_YEAR (default 2023),
PERSONA_REBUILD_CACHE=TRUE to rebuild the cache after downloading new data.

Results are written to /app/output/persona_predictions.csv and .xlsx.
EOF
}

require_open_data() {
    if [ ! -f "/data/cache/bag_verblijfsobjecten.csv" ] && [ ! -f "/data/bag-light.gpkg" ]; then
        echo "Error: no open data in /data. Mount a volume on /data and run the 'download' command first."
        exit 1
    fi
}

predict() {
    require_open_data
    mkdir -p /app/output
    # Run from /tmp so stray plot files do not end up in /app
    cd /tmp && exec Rscript /app/persona_assignment.R
}

case "$1" in
    help|--help|-h)
        usage
        ;;
    download)
        exec python3 /app/download_netherlands_data.py /data "$CBS_YEAR" "$INCOME_YEAR"
        ;;
    test)
        echo "R version: $(R --version | head -1)"
        Rscript -e "for (p in c('tidyverse', 'data.table', 'janitor', 'readxl', 'writexl', 'ranger', 'sf')) cat(sprintf('  %s: %s\n', p, packageVersion(p)))"
        Rscript -e "b <- readRDS('/app/models/persona_rf.rds'); cat(sprintf('Model: trained %s, n = %d, %d trees\n', b\$training\$date, b\$training\$n_obs, b\$training\$num_trees))"
        echo "Open data in /data:"
        ls -la /data
        ;;
    bash|shell)
        exec /bin/bash
        ;;
    Rscript)
        exec "$@"
        ;;
    "")
        echo "Using example addresses: /app/examples/addresses_example.csv"
        predict
        ;;
    *.csv|*.xlsx|*.xls)
        if [ ! -f "$1" ]; then
            echo "Error: address file $1 not found inside the container. Mount it with -v."
            exit 1
        fi
        export PERSONA_ADDRESSES="$1"
        predict
        ;;
    *)
        if [ $(( $# % 2 )) -ne 0 ]; then
            echo "Error: give postcode and house number pairs, e.g. 1011AB 12 2514JG 20. Use 'help' for usage."
            exit 1
        fi
        echo "postcode,huisnummer" > /tmp/addresses.csv
        while [ "$#" -gt 0 ]; do
            echo "$1,$2" >> /tmp/addresses.csv
            shift 2
        done
        export PERSONA_ADDRESSES=/tmp/addresses.csv
        predict
        ;;
esac
