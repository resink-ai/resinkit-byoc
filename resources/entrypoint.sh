#!/bin/bash

# Start Kafka
$KAFKA_HOME/bin/zookeeper-server-start.sh $KAFKA_HOME/config/zookeeper.properties &
$KAFKA_HOME/bin/kafka-server-start.sh $KAFKA_HOME/config/server.properties &

# Start Nginx (not needed for BYOC)
# nginx

# Start Flink session cluster & SQL gateway
$FLINK_HOME/bin/start-cluster.sh
$FLINK_HOME/bin/sql-gateway.sh start -Dsql-gateway.endpoint.rest.address=localhost

echo "starting resinkit at: $RESINKIT_JAR_PATH"
java -jar $RESINKIT_JAR_PATH
