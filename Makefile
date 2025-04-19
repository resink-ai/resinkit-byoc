SHELL = /bin/bash -x

.PHONY: all \
	resinkit-terra resinkit-terra-test resinkit-terra-build-mysql2doris \
	test-mysql2doris test-mysql2kafka build-mysql2kafka

all: jar download resinkit-terra

download:
	cd resources/flink/lib && bash download.sh

resinkit-terra:
	-docker stop resinkit.terra
	-docker rm resinkit.terra
	docker buildx build --platform linux/amd64,linux/arm64/v8 -t ai.resink.it.terra -f resinkit-terra/Dockerfile .
	docker run -d --name resinkit.terra -p 8602:8602 -p 9092:9092 -p 8083:8083 -p 8081:8081 ai.resink.it.terra

resinkit-terra-test:
	# kcat -b localhost:9092 -L
	# sleep 5
	docker exec resinkit.terra curl -s http://localhost:8081/config | jq .
	docker exec resinkit.terra curl -s http://localhost:8083/info | jq .

resinkit-terra-build-mysql2doris:
	docker-compose -f resinkit-terra/docker-compose-mysql2doris.yaml -p resinkit-terra-mysql2doris down
	docker-compose -f resinkit-terra/docker-compose-mysql2doris.yaml -p resinkit-terra-mysql2doris up --build --force-recreate -d

resinkit-terra-test-mysql2doris:
	docker exec -it resinkit-terra-mysql2doris-mysql-1 python /usr/local/bin/generate_data.py
	docker exec -it resinkit-terra-mysql2doris-flink-1 bash /opt/flink-cdc-3.2.1/bin/flink-cdc.sh /opt/flink/cdc/mysql_2_doris.yaml

## debugging commands:
# docker exec -it resinkit-terra-mysql2doris-mysql-1 mysql -u root -prootpassword mydatabase -e "show tables;"
# docker exec -it resinkit-terra-mysql2doris-mysql-1 mysql -u root -prootpassword mydatabase -e "select * from User"
# docker exec -it resinkit-terra-mysql2doris-doris-1 mysql -h 127.0.0.1 -uroot -P9030 mydatabase -e 'select * from User'

# resinkit-terra-build-mysql2kafka:
# 	docker-compose -f docker-compose-mysql2kafka.yaml -p resinkit-mysql2kafka down
# 	# docker-compose -f docker-compose-mysql2kafka.yaml -p resinkit-mysql2kafka down --volumes
# 	docker-compose -f docker-compose-mysql2kafka.yaml -p resinkit-mysql2kafka up --build --force-recreate -d

resinkit-terra-test-mysql2kafka:
	docker exec -it resinkit-terra-mysql2doris-mysql-1 python /usr/local/bin/generate_data.py
	docker exec -it resinkit-terra-mysql2doris-flink-1 bash /opt/flink-cdc-3.2.1/bin/flink-cdc.sh /opt/flink/cdc/mysql_2_kafka.yaml
	seleep 5
	docker exec -it resinkit-mysql2kafka-mysql-1 python /usr/local/bin/generate_data.py
	kcat -b localhost:9092 -L 
	kcat -C -b localhost:9092 -t mydatabase.User
