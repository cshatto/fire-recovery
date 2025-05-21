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
# Copy project files, including safe_rasters/
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt || { echo "pip install failed"; exit 1; }

FROM python:3.13-slim
# Set working directory
WORKDIR /fire-recovery

# Copy project files, including safe_rasters/
COPY . .

# Copy installed dependencies from builder
COPY --from=builder /root/.local /root/.local

# Modify msi_safe_l2a.yaml to change sensors: [msi] to sensors: [sen2_msi]
RUN sed -i 's/sensors: \[msi\]/sensors: \[sen2_msi\]/' /root/.local/lib/python3.13/site-packages/satpy/etc/readers/msi_safe_l2a.yaml

# Environment variables
ENV PYTHONPATH=/fire-recovery/scripts
ENV PATH=/root/.local/bin:$PATH