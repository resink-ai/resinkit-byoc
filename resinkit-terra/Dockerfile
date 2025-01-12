# Use platform-specific base image that will be automatically selected based on the target architecture
FROM --platform=$TARGETPLATFORM flink:1.19.1-scala_2.12-java17

# Install system dependencies
# These will be installed for whichever architecture is being built
RUN apt-get update && apt-get install -y \
    vim \
    wget \
    gnupg \
    nginx \
    python3-pip \
    python3-dev \
    libpcre3-dev \
    iputils-ping \
    mysql-client \
    telnet \
    bash \
    && apt-get clean

# Install Kafka
RUN wget https://archive.apache.org/dist/kafka/3.4.0/kafka_2.12-3.4.0.tgz -O /tmp/kafka.tgz \
    && tar -xzf /tmp/kafka.tgz -C /opt \
    && mv /opt/kafka_2.12-3.4.0 /opt/kafka \
    && rm /tmp/kafka.tgz

# Setup Kafka configuration
COPY resources/kafka/server.properties /opt/kafka/config/server.properties

# Download and install Flink CDC connectors
RUN wget https://dlcdn.apache.org/flink/flink-cdc-3.2.1/flink-cdc-3.2.1-bin.tar.gz -O /tmp/flink-cdc-3.2.1-bin.tar.gz \
    && tar -xzf /tmp/flink-cdc-3.2.1-bin.tar.gz -C /opt/ \
    && rm /tmp/flink-cdc-3.2.1-bin.tar.gz

# Copy all required JAR files for Flink CDC connectors
COPY resources/flink/lib/flink-cdc-pipeline-connector-mysql-3.2.1.jar /opt/flink-cdc-3.2.1/lib/
COPY resources/flink/lib/flink-cdc-pipeline-connector-kafka-3.2.1.jar /opt/flink-cdc-3.2.1/lib/
COPY resources/flink/lib/flink-cdc-pipeline-connector-doris-3.2.1.jar /opt/flink-cdc-3.2.1/lib/
COPY resources/flink/lib/mysql-connector-java-8.0.27.jar /opt/flink/lib/
COPY resources/flink/lib/paimon-flink-1.19-0.9.0.jar /opt/flink/lib/
COPY resources/flink/lib/paimon-flink-action-0.9.0.jar /opt/flink/lib/
COPY resources/flink/lib/flink-shaded-hadoop-2-uber-2.8.3-10.0.jar /opt/flink/lib/

# Copy ResinKit application
ARG RESINKIT_JAR=engines/java_app/target/resinkit-0.0.1-SNAPSHOT.jar
COPY ${RESINKIT_JAR} /root/app/resinkit.jar
ENV RESINKIT_JAR_PATH /root/app/resinkit.jar

# Configure Flink
COPY resources/flink/conf/conf.yaml /opt/flink/conf/config.yaml
COPY resources/flink/conf/log4j.properties /opt/flink/conf/log4j.properties
COPY resources/flink/cdc/ /opt/flink/cdc/

# Set up environment variables
ENV KAFKA_HOME=/opt/kafka
ENV JAVA_HOME=/opt/java/openjdk
ENV FLINK_HOME=/opt/flink
ENV PATH=$PATH:$KAFKA_HOME/bin:$FLINK_HOME/bin:$JAVA_HOME/bin

# Expose necessary ports
# ResinKit
EXPOSE 8000
# Kafka
EXPOSE 9092
# Flink web UI
EXPOSE 8081
# Flink SQL gateway
EXPOSE 8083
# JobManager RPC
EXPOSE 6123
# TaskManagers data ports
EXPOSE 6121-6130

# Copy and set entrypoint script
COPY resources/entrypoint.sh /opt/entrypoint.sh
RUN chmod +x /opt/entrypoint.sh
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
