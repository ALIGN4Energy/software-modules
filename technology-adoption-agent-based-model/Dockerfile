# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install required Python packages
RUN pip install --no-cache-dir \
    numpy==1.26.4 \
    pandas==2.2.0 \
    mesa==2.2.4

# Copy the ABM files
COPY ABM.py /app/
COPY run_abm.py /app/

# Copy entrypoint script
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh /app/run_abm.py

# Create output directory
RUN mkdir -p /app/output

# Set entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Default command - will be handled by entrypoint
CMD []
