# Use Ubuntu as the base image
FROM ubuntu:latest

# Install dependencies (assuming this part is okay)
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates make curl unzip wget

RUN GIT_TERMINAL_PROMPT=0 git clone https://github.com/resink-ai/resinkit-byoc.git /root/resinkit-byoc

# Set container environment variable
ENV IS_CONTAINER=true

# Change working directory
COPY resources/environment.seed /etc/environment.seed
WORKDIR /root/resinkit-byoc
RUN make install

# Expose necessary ports
# ResinKit
EXPOSE 8080
# Kafka
EXPOSE 9092
# Flink web UI
EXPOSE 8081
# Flink SQL gateway
EXPOSE 8083
# Jupyter
EXPOSE 8888
# ResinKit API
EXPOSE 8602
# # MinIO
# EXPOSE 9000
# # MariaDB
# EXPOSE 3306

# Keep container running with tail -f
# CMD ["tail", "-f", "/dev/null"]
ENTRYPOINT [ "/root/resinkit-byoc/resources/setup.sh" ]
CMD [ "run_entrypoint", "-f" ]

# docker stop resinkit
# docker rm resinkit
# docker buildx build --platform linux/amd64,linux/arm64/v8 -t ai.resink.kit -f Dockerfile .
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
