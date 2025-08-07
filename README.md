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

## VPS / Docker

```bash
docker run -d --name my-ubuntu -p 8080:8080 -p 9092:9092 -p 8081:8081 -p 8083:8083 -p 8888:8888 -p 8602:8602 -p 5000:5000 ubuntu tail -f /dev/null
# docker exec -it my-ubuntu bash
uv run pyinfra --sudo  -vvv --debug -y @docker/my-ubuntu deploy.all_in_one
```

## Developement Guide

### Publish new docker image

```shell
release_tag=release-1.19.alpha20250504
git tag $release_tag && git push origin $release_tag -f
```
