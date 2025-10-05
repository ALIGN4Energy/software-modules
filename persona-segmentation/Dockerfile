# Use rocker/r-ver for a stable R environment
FROM rocker/r-ver:4.5.1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libgdal-dev \
    libudunits2-dev \
    libproj-dev \
    libgeos-dev \
    python3 \
    python3-pip \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages for data downloading
RUN pip3 install --break-system-packages requests

# Set working directory
WORKDIR /app

# Install R packages
RUN R -e "install.packages(c('dplyr', 'readr', 'readxl', 'ggplot2', 'janitor', 'ranger', 'caret', 'missForest', 'data.table', 'stringr'), repos='https://cran.rstudio.com/')"

# Copy the download script
COPY download_netherlands_data.py /app/

# Copy the training data files (these are required)
# Note: confidential_data/ directory must exist locally but is gitignored
COPY confidential_data/output.csv /app/confidential_data/
COPY confidential_data/data_long_4c.xls /app/confidential_data/

# Download CBS and BAG data during build
RUN python3 download_netherlands_data.py

# Copy the R script
COPY Datasegmentation.Rmd /app/

# Create an executable R script from the RMD chunks
RUN echo '#!/usr/bin/env Rscript' > /app/run_datasegmentation.R && \
    echo 'library(data.table)' >> /app/run_datasegmentation.R && \
    echo 'library(dplyr)' >> /app/run_datasegmentation.R && \
    echo 'library(readxl)' >> /app/run_datasegmentation.R && \
    echo 'library(readr)' >> /app/run_datasegmentation.R && \
    echo 'library(missForest)' >> /app/run_datasegmentation.R && \
    echo 'library(ranger)' >> /app/run_datasegmentation.R && \
    echo 'library(caret)' >> /app/run_datasegmentation.R && \
    echo 'library(stringr)' >> /app/run_datasegmentation.R && \
    echo 'library(ggplot2)' >> /app/run_datasegmentation.R && \
    echo '' >> /app/run_datasegmentation.R && \
    echo '# Accept command line arguments for addresses' >> /app/run_datasegmentation.R && \
    echo 'args <- commandArgs(trailingOnly = TRUE)' >> /app/run_datasegmentation.R && \
    echo 'if (length(args) >= 2) {' >> /app/run_datasegmentation.R && \
    echo '  user_postcodes <- args[1:2]' >> /app/run_datasegmentation.R && \
    echo '  user_numbers <- if(length(args) >= 4) args[3:4] else c("1", "1")' >> /app/run_datasegmentation.R && \
    echo '} else {' >> /app/run_datasegmentation.R && \
    echo '  user_postcodes <- c("2051ER", "2051NA")' >> /app/run_datasegmentation.R && \
    echo '  user_numbers <- c("2", "13-D")' >> /app/run_datasegmentation.R && \
    echo '}' >> /app/run_datasegmentation.R

# Add the main script content
COPY run_datasegmentation_main.R /app/
RUN cat /app/run_datasegmentation_main.R >> /app/run_datasegmentation.R

# Copy and set up entrypoint
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh /app/run_datasegmentation.R

# Create output directory
RUN mkdir -p /app/output

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command - will be handled by entrypoint
CMD []