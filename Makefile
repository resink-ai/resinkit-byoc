SHELL = /bin/bash -x

.PHONY: all resinkit-terra

all: download resinkit-terra

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
	cp -v resources/environment.seed /etc/environment.seed
	bash resources/setup.sh debian_install_all

install_additional:
	bash resources/setup.sh debian_install_additional

run_production:
	ENV=production bash resources/setup.sh run_entrypoint
	# FORCE_RESTART=true ENV=byoc bash resources/setup.sh run_entrypoint
	bash resources/setup.sh run_curl_test || true

run_byoc:
	ENV=byoc bash resources/setup.sh run_entrypoint
	# FORCE_RESTART=true ENV=byoc bash resources/setup.sh run_entrypoint
	bash resources/setup.sh run_curl_test || true


# Deploy with pyinfra
deploy:
	# apt-get update && apt-get install -y --no-install-recommends git ca-certificates make curl unzip wget
	# git clone https://github.com/resink-ai/resinkit-byoc.git
	# cd resinkit-byoc
	bash resources/setup_uv.sh
	/opt/uv/uv run pyinfra @local deploy.deploy_all
	# /opt/uv/uv run pyinfra @local deploy.install_00_prep
	# /opt/uv/uv run pyinfra @local deploy.install_01_core
	# /opt/uv/uv run pyinfra @local deploy.install_02_core_su
	# /opt/uv/uv run pyinfra @local deploy.install_03_flink