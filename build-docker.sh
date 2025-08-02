#!/bin/bash

# 构建脚本：确保在正确的架构上编译libimgsmlr

set -e

echo "开始构建 imgsmlr-server Docker 镜像..."

# 检查是否在正确的目录
if [ ! -f "Dockerfile" ]; then
    echo "错误：请在 imgsmlr-server 目录下运行此脚本"
    exit 1
fi

# 构建Docker镜像
echo "使用 buildx 构建多架构镜像..."
docker buildx build \
    --platform linux/amd64 \
    --tag jie123108/imgsmlr-server:latest \
    --tag jie123108/imgsmlr-server:$(date +%Y%m%d) \
    --push \
    .

echo "构建完成！"
echo "镜像标签："
echo "  - jie123108/imgsmlr-server:latest"
echo "  - jie123108/imgsmlr-server:$(date +%Y%m%d)" 