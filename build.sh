#!/usr/bin/env bash

DHIMAGE=$1
TAG=$2
echo "Building multi-arch image $DHIMAGE:$TAG and pushing to Docker Hub"
ARCHS=$(ls -1 Dockerfile* | awk -F. '{print $2}')
for ARCH in $ARCHS; do
    echo "Building for $ARCH"
    docker build -f Dockerfile.${ARCH} -t ${DHIMAGE}:${ARCH}-${TAG} .
    docker tag ${DHIMAGE}:${ARCH}-${TAG} ${DHIMAGE}:${ARCH}-latest
    docker push ${DHIMAGE}:${ARCH}-${TAG}
    docker push ${DHIMAGE}:${ARCH}-latest
done

echo "Creating Docker multiarch manifest ${DHIMAGE}:latest"
docker manifest create -a ${DHIMAGE}:latest ${DHIMAGE}:amd64-latest ${DHIMAGE}:arm32v7-latest ${DHIMAGE}:arm64v8-latest
docker manifest annotate ${DHIMAGE}:latest ${DHIMAGE}:arm32v7-latest --arch arm --os linux
docker manifest annotate ${DHIMAGE}:latest ${DHIMAGE}:arm64v8-latest --arch arm64 --variant v8 --os linux
docker manifest push ${DHIMAGE}:latest

echo "Creating Docker multiarch manifest ${DHIMAGE}:${TAG}"
docker manifest create -a ${DHIMAGE}:${TAG} ${DHIMAGE}:amd64-${TAG} ${DHIMAGE}:arm32v7-${TAG} ${DHIMAGE}:arm64v8-${TAG}
docker manifest annotate ${DHIMAGE}:${TAG} ${DHIMAGE}:arm32v7-${TAG} --arch arm --os linux
docker manifest annotate ${DHIMAGE}:${TAG} ${DHIMAGE}:arm64v8-${TAG} --arch arm64 --variant v8 --os linux
docker manifest push ${DHIMAGE}:${TAG}