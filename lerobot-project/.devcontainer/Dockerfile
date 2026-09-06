FROM ros:humble-perception

ENV DEBIAN_FRONTEND=noninteractive

# -------------------------------------------------
# System Packages
# -------------------------------------------------
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    python3-setuptools \
    python3-wheel \
    git \
    curl \
    wget \
    unzip \
    vim \
    build-essential \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# pip 업그레이드
RUN python3 -m pip install --upgrade pip setuptools wheel

# Python 라이브러리 설치
RUN pip install \
    pandas \
    numpy \
    scipy \
    pyarrow \
    pillow \
    opencv-python \
    h5py \
    zarr \
    datasets \
    huggingface_hub \
    lerobot \
    jupyter \
    ipykernel

# Jupyter Kernel 등록
RUN python3 -m ipykernel install --user \
    --name lerobot \
    --display-name "Python (LeRobot)"

# 작업 폴더
WORKDIR /workspaces/lerobot-project

CMD ["/bin/bash"]