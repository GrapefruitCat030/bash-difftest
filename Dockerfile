FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace

RUN apt-get update && \
    apt-get install -y \
      build-essential \
      wget \
      git \
      python3 \
      python3-pip \
      automake \
      autoconf \
      libtool \
      pkg-config \
      lcov \
      default-jre \
      uuid-dev \
      curl \
      ca-certificates \
      # nodejs/npm for tree-sitter-bash
      nodejs \
      npm \
      vim \
      less \
      sudo

COPY . /workspace

RUN pip3 install --upgrade pip && \
    pip3 install -r requirements.txt

WORKDIR /workspace

CMD ["/bin/bash"]