SHELL = /bin/bash -x

.PHONY: all resinkit-terra

all: download resinkit-terra

CURRENT_DIR := $(shell pwd)

download:
	cd resources/flink/lib && bash download.sh

resinkit-terra:
	-docker stop resinkit.terra
	-docker rm resinkit.terra
	docker buildx build -t ai.resink.it.terra -f resinkit-terra/Dockerfile .
	docker run -d --name resinkit.terra -p 8080:8080 -p 9092:9092 -p 8083:8083 -p 8081:8081 ai.resink.it.terra

resinkit-terra-mysql-mionio:
	-docker-compose -f resinkit-terra/docker-compose-mysql-mionio.yaml -p resinkit-mysql-mionio down
	docker-compose -f resinkit-terra/docker-compose-mysql-mionio.yaml -p resinkit-mysql-mionio up -d

install:
	ROOT_DIR=$(CURRENT_DIR) RESINKIT_BYOC_RELEASE_BRANCH=master bash resinkit_byoc/scripts/pre_install.sh
	/opt/uv/uv run pyinfra @local deploy.deploy_all -y

run_production:
	bash resinkit_byoc/scripts/drop_privs_run.sh

run_byoc:
	ENV=byoc bash resinkit_byoc/scripts/drop_privs_run.sh
