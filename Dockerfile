FROM docker.io/pytorch/pytorch

ARG gh_username=kddresearch
ARG gh_repo=nl-EasyOCR
ARG service_home="/home/EasyOCR"

# System deps
RUN apt-get update -y && \
    apt-get install -y \
      libglib2.0-0 \
      libsm6 \
      libxext6 \
      libxrender-dev \
      libgl1-mesa-dev \
      git && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/*

# Clone & install EasyOCR
RUN mkdir -p "$service_home" && \
    git clone "https://github.com/$gh_username/$gh_repo.git" "$service_home" && \
    cd "$service_home" && \
    git remote add upstream "https://github.com/$gh_username/$gh_repo.git" && \
    git pull upstream master && \
    python -m pip install --upgrade pip && \
    python "$service_home/setup.py" build_ext --inplace -j4 && \
    python -m pip install -e "$service_home"

# Install FastAPI + Uvicorn + upload parser
RUN python -m pip install \
      fastapi \
      "uvicorn[standard]" \
      python-multipart

# Copy our server
WORKDIR /app
COPY server.py .

EXPOSE 80
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "80"]