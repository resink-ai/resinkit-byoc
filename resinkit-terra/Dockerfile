# Use a multi-stage build to support multiple architectures
FROM --platform=linux/amd64 flink:1.19.1-scala_2.12-java17 AS builder-amd64

# Install dependencies
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
    && apt-get clean

# Install Kafka
RUN wget https://archive.apache.org/dist/kafka/3.4.0/kafka_2.12-3.4.0.tgz -O /tmp/kafka.tgz \
    && tar -xzf /tmp/kafka.tgz -C /opt \
    && mv /opt/kafka_2.12-3.4.0 /opt/kafka \
    && rm /tmp/kafka.tgz

# Setup environment variables for Kafka
COPY resources/kafka/server.properties /opt/kafka/config/server.properties


# Download and install Flink CDC connectors
RUN wget https://dlcdn.apache.org/flink/flink-cdc-3.2.1/flink-cdc-3.2.1-bin.tar.gz -O /tmp/flink-cdc-3.2.1-bin.tar.gz \
    && tar -xzf /tmp/flink-cdc-3.2.1-bin.tar.gz -C /opt/ \
    && rm /tmp/flink-cdc-3.2.1-bin.tar.gz

# Download additional JAR packages for Flink CDC connectors
COPY resources/flink/lib/flink-cdc-pipeline-connector-mysql-3.2.1.jar /opt/flink-cdc-3.2.1/lib/
COPY resources/flink/lib/flink-cdc-pipeline-connector-kafka-3.2.1.jar /opt/flink-cdc-3.2.1/lib/
COPY resources/flink/lib/flink-cdc-pipeline-connector-doris-3.2.1.jar /opt/flink-cdc-3.2.1/lib/
COPY resources/flink/lib/mysql-connector-java-8.0.27.jar /opt/flink/lib/
COPY resources/flink/lib/paimon-flink-1.19-0.9.0.jar /opt/flink/lib/
COPY resources/flink/lib/paimon-flink-action-0.9.0.jar /opt/flink/lib/
COPY resources/flink/lib/flink-shaded-hadoop-2-uber-2.8.3-10.0.jar /opt/flink/lib/


# Build for arm64v8
FROM --platform=linux/arm64/v8 flink:1.19.1-scala_2.12-java17 AS builder-arm64v8

# Install dependencies
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
    && apt-get clean

# Install Kafka
RUN wget https://archive.apache.org/dist/kafka/3.4.0/kafka_2.12-3.4.0.tgz -O /tmp/kafka.tgz \
    && tar -xzf /tmp/kafka.tgz -C /opt \
    && mv /opt/kafka_2.12-3.4.0 /opt/kafka \
    && rm /tmp/kafka.tgz

# Setup environment variables for Kafka
COPY resources/kafka/server.properties /opt/kafka/config/server.properties

# Download and install Flink CDC connectors
RUN wget https://dlcdn.apache.org/flink/flink-cdc-3.2.1/flink-cdc-3.2.1-bin.tar.gz -O /tmp/flink-cdc-3.2.1-bin.tar.gz \
    && tar -xzf /tmp/flink-cdc-3.2.1-bin.tar.gz -C /opt/ \
    && rm /tmp/flink-cdc-3.2.1-bin.tar.gz

# Download additional JAR packages for Flink CDC connectors
COPY resources/flink/lib/flink-cdc-pipeline-connector-mysql-3.2.1.jar /opt/flink-cdc-3.2.1/lib/
COPY resources/flink/lib/flink-cdc-pipeline-connector-kafka-3.2.1.jar /opt/flink-cdc-3.2.1/lib/
COPY resources/flink/lib/flink-cdc-pipeline-connector-doris-3.2.1.jar /opt/flink-cdc-3.2.1/lib/
COPY resources/flink/lib/mysql-connector-java-8.0.27.jar /opt/flink/lib/
COPY resources/flink/lib/paimon-flink-1.19-0.9.0.jar /opt/flink/lib/
COPY resources/flink/lib/paimon-flink-action-0.9.0.jar /opt/flink/lib/
COPY resources/flink/lib/flink-shaded-hadoop-2-uber-2.8.3-10.0.jar /opt/flink/lib/


# Create the final image for both architectures
FROM scratch AS final
COPY --from=builder-amd64 / /
COPY --from=builder-arm64v8 / /

# Rest of your Dockerfile ...

ARG RESINKIT_JAR=engines/java_app/target/resinkit-0.0.1-SNAPSHOT.jar
COPY ${RESINKIT_JAR} /root/app/resinkit.jar
ENV RESINKIT_JAR_PATH /root/app/resinkit.jar

###################### FLINK ######################
COPY resources/flink/conf/conf.yaml /opt/flink/conf/config.yaml
COPY resources/flink/conf/log4j.properties /opt/flink/conf/log4j.properties
COPY resources/flink/cdc/ /opt/flink/cdc/

# # see https://nightlies.apache.org/flink/flink-docs-master/docs/dev/table/materialized-table/quickstart/
# ENV CATALOG_STORE_PATH=/tmp/flink/catalog-store
# ENV CATALOG_PATH=/tmp/flink/catalog
# ENV DEFAULT_DB_PATH=/tmp/flink/mydb
# ENV CHECKPOINTS_PATH=/tmp/flink/checkpoints
# ENV SAVEPOINTS_PATH=/tmp/flink/savepoints
# RUN mkdir -p $CATALOG_STORE_PATH $CATALOG_PATH $DEFAULT_DB_PATH $CHECKPOINTS_PATH $SAVEPOINTS_PATH

ENV KAFKA_HOME /opt/kafka
ENV PATH $PATH:$KAFKA_HOME/bin

# Nginx config (optional)
# RUN rm /etc/nginx/sites-enabled/default
# COPY resources/nginx/resinkit_nginx.conf /etc/nginx/conf.d/default.conf

# Expose RESINKIT port
EXPOSE 8000
# Expose Kafka port
EXPOSE 9092
# Expose Flink web UI port
EXPOSE 8081
# Expose Flink SQL gateway port
EXPOSE 8083
# Expose JobManager's RPC port
EXPOSE 6123
# Expose TaskManagers' data port
EXPOSE 6121-6130

ENV JAVA_HOME=/opt/java/openjdk
ENV FLINK_HOME /opt/flink
ENV PATH $PATH:$FLINK_HOME/bin:$JAVA_HOME/bin

# Copy entrypoint script
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
