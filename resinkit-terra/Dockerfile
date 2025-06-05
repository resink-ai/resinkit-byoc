# Use Ubuntu as the base image
FROM ubuntu:latest

# Build arguments - can be customized at build time
ARG RESINKIT_ROLE=resinkit
ARG RESINKIT_ROLE_HOME=/home/resinkit
ARG FLINK_HOME=/opt/flink
ARG FLINK_CDC_HOME=/opt/flink-cdc
ARG RESINKIT_API_PATH=/opt/resinkit/api
ARG RESINKIT_API_SERVICE_PORT=8602
ARG KAFKA_HOME=/opt/kafka
ARG MYSQL_RESINKIT_PASSWORD=resinkit_inspect_password
ARG MINIO_ROOT_USER=minio
ARG MINIO_ROOT_PASSWORD=minio123
ARG MINIO_DATA_DIR=/opt/minio/data
ARG MINIO_CONFIG_DIR=/opt/minio/config
ARG MINIO_CONSOLE_PORT=9001
ARG MINIO_API_PORT=9000

# Convert build arguments to environment variables so they persist in the container
ENV RESINKIT_ROLE=${RESINKIT_ROLE}
ENV RESINKIT_ROLE_HOME=${RESINKIT_ROLE_HOME}
ENV FLINK_HOME=${FLINK_HOME}
ENV FLINK_CDC_HOME=${FLINK_CDC_HOME}
ENV RESINKIT_API_PATH=${RESINKIT_API_PATH}
ENV RESINKIT_API_SERVICE_PORT=${RESINKIT_API_SERVICE_PORT}
ENV KAFKA_HOME=${KAFKA_HOME}
ENV MYSQL_RESINKIT_PASSWORD=${MYSQL_RESINKIT_PASSWORD}
ENV MINIO_ROOT_USER=${MINIO_ROOT_USER}
ENV MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}
ENV MINIO_DATA_DIR=${MINIO_DATA_DIR}
ENV MINIO_CONFIG_DIR=${MINIO_CONFIG_DIR}
ENV MINIO_CONSOLE_PORT=${MINIO_CONSOLE_PORT}
ENV MINIO_API_PORT=${MINIO_API_PORT}
ENV MINIO_ENDPOINT=http://127.0.0.1:${MINIO_API_PORT}

# Install dependencies (assuming this part is okay)
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates make curl unzip wget

RUN GIT_TERMINAL_PROMPT=0 git clone https://github.com/resink-ai/resinkit-byoc.git /root/resinkit-byoc

# Change working directory
WORKDIR /root/resinkit-byoc
RUN make install

# TODO: allow customizing the variables

# Expose necessary ports
# ResinKit
EXPOSE 8080
# Kafka
EXPOSE 9092
# Flink web UI
EXPOSE 8081
# Flink SQL gateway
EXPOSE 8083
# MinIO
EXPOSE 9000
# MariaDB
EXPOSE 3306

# Keep container running with tail -f
# CMD ["tail", "-f", "/dev/null"]
ENTRYPOINT [ "/root/resinkit-byoc/resources/setup.sh" ]
CMD [ "run_entrypoint", "-f" ]

# docker stop resinkit
# docker rm resinkit
# docker buildx build --platform linux/amd64,linux/arm64/v8 -t ai.resink.kit -f Dockerfile .
## docker build --platform linux/amd64,linux/arm64/v8 -t ai.resink.kit -f Dockerfile --build-arg RESINKIT_JAR=app/target/resinkit-0.0.1-SNAPSHOT.jar .
# docker run -d --name resinkit -p 8000:8000 -p 9092:9092 -p 8083:8083 -p 8081:8081 ai.resink.kit

# Examples of using build arguments:
# docker buildx build --platform linux/amd64,linux/arm64/v8 \
#   --build-arg RESINKIT_ROLE=customuser \
#   --build-arg MINIO_ROOT_PASSWORD=mysecurepassword \
#   --build-arg RESINKIT_API_SERVICE_PORT=8700 \
#   -t ai.resink.kit -f Dockerfile .

# curl -H 'x-resinkit-token: demo' localhost:8000/hello
# [Test Kafka Connection] # kcat -b localhost:9092 -L
# [Create Kafka Topic]    # kcat -b localhost:9092 -L -t node_1_feed_config
# [Consume Kafka MSG]     # kcat -b localhost:9092 -L -G my_group -o earliest node_1_feed_config
# [Test Flink Rest API]   # docker exec resinkit curl -s http://localhost:8081/config | jq .
# [View Flink Jobs]       # docker exec resinkit curl -s http://localhost:8081/jobs | jq .
# [Test Flink gateway]    # docker exec resinkit curl -s http://localhost:8083/info | jq .
