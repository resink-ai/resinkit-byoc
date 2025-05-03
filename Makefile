SHELL = /bin/bash -x

.PHONY: all resinkit-terra

all: download resinkit-terra

download:
	cd resources/flink/lib && bash download.sh

resinkit-terra:
	-docker stop resinkit.terra
	-docker rm resinkit.terra
	docker buildx build --platform linux/amd64,linux/arm64/v8 \
		-t ai.resink.it.terra -f resinkit-terra/Dockerfile .
	docker run -d --name resinkit.terra -p 8080:8080 -p 9092:9092 -p 8083:8083 -p 8081:8081 ai.resink.it.terra

install:
	bash resources/setup_debian.sh

run:
	bash resources/setup.sh run_entrypoint
