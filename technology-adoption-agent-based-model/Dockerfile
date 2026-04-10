# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install required Python packages
RUN pip install --no-cache-dir \
    numpy \
    pandas \
    mesa \
    networkx

# Copy the ABM files
COPY ABM.py /app/
COPY run_abm.py /app/

# Copy tutorial data files
COPY tutorial_households.csv /app/
COPY tutorial_technologies.csv /app/

# Copy entrypoint script
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh /app/run_abm.py

# Create output directory
RUN mkdir -p /app/output

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command - will be handled by entrypoint
CMD []
