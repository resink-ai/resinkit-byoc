# Use Ubuntu as the base image
FROM --platform=$TARGETPLATFORM ubuntu:latest

# Create setup script
RUN mkdir -p /opt/setup

COPY <<EOF /opt/entrypoint.sh
#!/bin/bash
set -x
echo "Starting user data script execution..."
apt-get update
apt-get install -y --no-install-recommends git ca-certificates make
echo "Cloning repository..."
git clone https://github.com/resink-ai/resinkit-byoc.git $HOME/resinkit-byoc
echo "Running setup script..."
cd $HOME/resinkit-byoc && ./resources/setup.sh debian_all
echo "User data script completed."
EOF

RUN chmod +x /opt/entrypoint.sh
# Expose necessary ports
# ResinKit
EXPOSE 8000
# Kafka
EXPOSE 9092
# Flink web UI
EXPOSE 8081
# Flink SQL gateway
EXPOSE 8083

# Set entrypoint script
ENTRYPOINT ["/opt/entrypoint.sh"]

# docker stop resinkit 
# docker rm resinkit
# docker buildx build --platform linux/amd64,linux/arm64/v8 -t ai.resink.kit -f Dockerfile .
## docker build --platform linux/amd64,linux/arm64/v8 -t ai.resink.kit -f Dockerfile --build-arg RESINKIT_JAR=app/target/resinkit-0.0.1-SNAPSHOT.jar .
# docker run -d --name resinkit -p 8000:8000 -p 9092:9092 -p 8083:8083 -p 8081:8081 ai.resink.kit

# curl -H 'x-resinkit-token: demo' localhost:8000/hello
# [Test Kafka Connection] # kcat -b localhost:9092 -L
# [Create Kafka Topic]    # kcat -b localhost:9092 -L -t node_1_feed_config
# [Consume Kafka MSG]     # kcat -b localhost:9092 -L -G my_group -o earliest node_1_feed_config
# [Test Flink Rest API]   # docker exec resinkit curl -s http://localhost:8081/config | jq .
# [View Flink Jobs]       # docker exec resinkit curl -s http://localhost:8081/jobs | jq .
# [Test Flink gateway]    # docker exec resinkit curl -s http://localhost:8083/info | jq .
