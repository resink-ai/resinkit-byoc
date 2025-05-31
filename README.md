# Quick start

## Docker

### From published docker image

Pre-requisite: docker and logged in to ghcr.io: `docker login ghcr.io`

```bash
# Download image from ghcr.io and run
docker run -d ghcr.io/resink-ai/resinkit-byoc:ai.resink.it.terra

# start a container without starting services
docker run -d ghcr.io/resink-ai/resinkit-byoc:ai.resink.it.terra run_tail_f
```

### Build docker locally

Pre-requisite: `docker` and `git` command installed.

```bash
git clone https://github.com/resink-ai/resinkit-byoc.git
cd resinkit-byoc
make resinkit-terra
```

## VPS (Debian based Image)

```bash
apt-get update && apt-get install -y --no-install-recommends git ca-certificates make curl unzip wget
git clone https://github.com/resink-ai/resinkit-byoc.git
cd resinkit-byoc
make install
make run_byoc
```

## Developement Guide

### Publish new docker image

```shell
release_tag=release-1.19.alpha20250504
git tag $release_tag && git push origin $release_tag -f
```
