SHELL := /bin/bash
REGISTRY ?= ghcr.io
IMG ?= jgibbarduk/route53dynip
VERSION ?= 1.0.0

# Architectures we can build for
ARCHES = linux/amd64,linux/arm/v7,linux/arm64

.PHONY: update-base
update-base:
	base=$$(grep FROM Dockerfile | awk '{print $$2}') ;\
	docker pull $$base

.PHONY: docker-build-local
docker-build-local:
	docker build -f Dockerfile -t $(REGISTRY)/$(IMG):$(VERSION) . ;\
	docker tag $(REGISTRY)/$(IMG):$(VERSION) $(IMG):latest ;\

.PHONY: docker-push
docker-push: docker-build-local
	docker push $(REGISTRY)/$(IMG):$(VERSION) ;\
	docker push $(REGISTRY)/$(IMG):latest

.PHONY: docker-multiarch
docker-multiarch:
	docker buildx create --use ;\
	docker buildx build --platform $(ARCHES) -t $(IMG):$(VERSION) -t $(IMG):latest --push . ;\
	docker buildx rm

.PHONY: clean
clean:
	docker rmi $(IMG):$(VERSION) || true ;\
	docker rmi $(IMG):latest || true
