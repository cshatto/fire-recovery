# Stage 1: Build dependencies
FROM python:3.13-slim AS builder

# Install build dependencies for GDAL and others
RUN apt-get update -y || { echo "apt-get update failed"; exit 1; } \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libgdal-dev \
        gdal-bin \
        ffmpeg \
        libproj-dev \
        libgeos-dev \
        libtiff-dev \
        libpq-dev \
        libjpeg-dev \
        g++ \
    || { echo "apt-get install failed"; exit 1; } \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /fire-recovery

# Copy requirements.txt
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt || { echo "pip install failed"; exit 1; }

# Stage 2: Final image
FROM python:3.13-slim

# Install runtime dependencies
RUN apt-get update -y || { echo "apt-get update failed"; exit 1; } \
    && apt-get install -y --no-install-recommends \
        libgdal-dev \
        gdal-bin \
        ffmpeg \
        libproj-dev \
        libgeos-dev \
        libtiff-dev \
        libpq-dev \
        libjpeg-dev \
    || { echo "apt-get install failed"; exit 1; } \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /fire-recovery

# Copy installed dependencies from builder
COPY --from=builder /root/.local /root/.local

# Modify msi_safe_l2a.yaml to change sensors: [msi] to sensors: [sen2_msi]
RUN sed -i 's/sensors: \[msi\]/sensors: \[sen2_msi\]/' /root/.local/lib/python3.13/site-packages/satpy/etc/readers/msi_safe_l2a.yaml

# Copy project files, including safe_rasters/
COPY scripts/ ./scripts/
COPY data/safe_rasters/ ./data/safe_rasters/
COPY requirements.txt .

# Ensure scripts are executable
RUN chmod +x scripts/*.py

# Environment variables
ENV PYTHONPATH=/fire-recovery/scripts
ENV PATH=/root/.local/bin:$PATH

# No volume mount since data is included
# Entry point
CMD ["python3", "scripts/main.py"]