# Use Ubuntu 18.04 as the base image
FROM ubuntu:18.04

# Set noninteractive mode to avoid prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Update and install dependencies
RUN apt-get update && apt-get install -y \
    # build-essential \
    # cmake \
    # git \
    # wget \
    # unzip \
    # libpng-dev \
    # libtiff-dev \
    # libjpeg-dev \
    # zlib1g-dev \
    # libdcmtk-dev \
    # libgdcm2-dev \
    # libtclap-dev \
    # qt5-default \
    # qtbase5-dev \
    # libvtk6-dev \
    xmedcon \
    nifti2dicom \
    && rm -rf /var/lib/apt/lists/*

# --- Verification ---
RUN nifti2dicom --help || true && \
    medcon --version || true

# Set default working directory
WORKDIR /data

# Default command
CMD ["/bin/bash"]
