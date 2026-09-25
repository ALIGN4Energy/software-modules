# rocker/r-ver 4.6.0 has the R and ranger versions the model was trained with (R 4.6.0, ranger 0.18.0)
FROM rocker/r-ver:4.6.0

# Install system dependencies (GDAL, GEOS and PROJ for reading the BAG geopackage with sf)
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libgdal-dev \
    libudunits2-dev \
    libproj-dev \
    libgeos-dev \
    python3 \
    python3-requests \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install R packages
RUN R -e "install.packages(c('tidyverse', 'data.table', 'janitor', 'readxl', 'writexl', 'ranger', 'sf', 'knitr'))"

# Copy the pipeline, the trained model and the example addresses
COPY download_netherlands_data.py persona_assignment.Rmd /app/
COPY models/ /app/models/
COPY examples/ /app/examples/

# Turn the R Markdown into a plain R script
RUN Rscript -e "knitr::purl('persona_assignment.Rmd', output = 'persona_assignment.R', quiet = TRUE)"

# Copy and set up entrypoint
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Open data and its cache live on a volume; results go to /app/output
ENV PERSONA_REPO_DIR=/app \
    PERSONA_DATA_DIR=/data \
    PERSONA_OUTPUT_DIR=/app/output
RUN mkdir -p /app/output /data
VOLUME ["/data"]

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command - will be handled by entrypoint
CMD []
