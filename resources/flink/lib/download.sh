#!/bin/bash

set -eo pipefail

download_and_extract() {
    url="$1"
    filename="$(basename "$url")"
    
    # Check if file already exists
    if [ -f "$filename" ]; then
        echo "File $filename already exists, skipping download"
    else
        echo "Downloading from URL: $url"
        # Download the file
        if ! wget -q "$url" -O "$filename"; then
            echo "Error: Failed to download $url"
            return 1
        fi
    fi
    
    # Extract based on file extension
    case "$filename" in
        *.tar.gz|*.tgz)
            tar -xzf "$filename"
            ;;
        *.tar.bz2|*.tbz2)
            tar -xjf "$filename"
            ;;
        *.tar.xz)
            tar -xJf "$filename"
            ;;
        *.tar)
            tar -xf "$filename"
            ;;
        *.zip)
            unzip -q "$filename"
            ;;
        *)
            echo "File $filename is not an archive or has unsupported format"
            return 0
            ;;
    esac
    
    # Check if extraction was successful
    if [ $? -eq 0 ]; then
        echo "Successfully extracted $filename"
        rm "$filename"
    else
        echo "Failed to extract $filename"
        return 1
    fi
}

# See: https://flink.apache.org/downloads/
FLINK_CONNECTOR_URLS=(
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-aws-kinesis-firehose/5.0.0-1.19/flink-connector-aws-kinesis-firehose-5.0.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-aws-kinesis-streams/5.0.0-1.19/flink-connector-aws-kinesis-streams-5.0.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-kinesis/5.0.0-1.19/flink-connector-kinesis-5.0.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-dynamodb/5.0.0-1.19/flink-connector-dynamodb-5.0.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-sqs/5.0.0-1.19/flink-connector-sqs-5.0.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-cassandra_2.12/3.2.0-1.19/flink-connector-cassandra_2.12-3.2.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-gcp-pubsub/3.1.0-1.19/flink-connector-gcp-pubsub-3.1.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-hbase-base/4.0.0-1.19/flink-connector-hbase-base-4.0.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-jdbc/3.2.0-1.19/flink-connector-jdbc-3.2.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-kafka/3.3.0-1.19/flink-connector-kafka-3.3.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-mongodb/1.2.0-1.19/flink-connector-mongodb-1.2.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-opensearch2/2.0.0-1.19/flink-connector-opensearch2-2.0.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-prometheus/1.0.0-1.19/flink-connector-prometheus-1.0.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-pulsar/4.1.0-1.18/flink-connector-pulsar-4.1.0-1.18.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-files/1.19.1/flink-connector-files-1.19.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-datagen/1.19.1/flink-connector-datagen-1.19.1.jar
)

FLINK_SQL_CONNECTOR_URLS=(
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-dynamodb/5.0.0-1.19/flink-sql-connector-dynamodb-5.0.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-aws-kinesis-firehose/5.0.0-1.19/flink-sql-connector-aws-kinesis-firehose-5.0.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-aws-kinesis-streams/5.0.0-1.19/flink-sql-connector-aws-kinesis-streams-5.0.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kinesis/4.3.0-1.19/flink-sql-connector-kinesis-4.3.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-elasticsearch6_2.12/1.9.1/flink-sql-connector-elasticsearch6_2.12-1.9.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-hbase-2.2/4.0.0-1.19/flink-sql-connector-hbase-2.2-4.0.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-hive-3.1.3_2.12/1.19.1/flink-sql-connector-hive-3.1.3_2.12-1.19.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.3.0-1.19/flink-sql-connector-kafka-3.3.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-mongodb/1.2.0-1.19/flink-sql-connector-mongodb-1.2.0-1.19.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-opensearch/1.2.0-1.19/flink-sql-connector-opensearch-1.2.0-1.19.jar
)

# https://github.com/apache/flink-cdc/releases/tag/release-3.2.1
FLINK_CDC_PIPELINE_CONNECTOR_3_2_1=(
    https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-mysql/3.2.1/flink-cdc-pipeline-connector-mysql-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-doris/3.2.1/flink-cdc-pipeline-connector-doris-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-starrocks/3.2.1/flink-cdc-pipeline-connector-starrocks-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-kafka/3.2.1/flink-cdc-pipeline-connector-kafka-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-paimon/3.2.1/flink-cdc-pipeline-connector-paimon-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-elasticsearch/3.2.1/flink-cdc-pipeline-connector-elasticsearch-3.2.1.jar
)

FLINK_CONNECTOR_CDC_3_2_1=(
    # https://repo1.maven.org/maven2/org/apache/flink/flink-connector-debezium/3.2.1/flink-connector-debezium-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-db2-cdc/3.2.1/flink-connector-db2-cdc-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-mongodb-cdc/3.2.1/flink-connector-mongodb-cdc-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-mysql-cdc/3.2.1/flink-connector-mysql-cdc-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-oracle-cdc/3.2.1/flink-connector-oracle-cdc-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-postgres-cdc/3.2.1/flink-connector-postgres-cdc-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-sqlserver-cdc/3.2.1/flink-connector-sqlserver-cdc-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-tidb-cdc/3.2.1/flink-connector-tidb-cdc-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-oceanbase-cdc/3.2.1/flink-connector-oceanbase-cdc-3.2.1.jar
)

FLINK_SQL_CONNECTOR_CDC_3_2_1=(
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-db2-cdc/3.2.1/flink-sql-connector-db2-cdc-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-mongodb-cdc/3.2.1/flink-sql-connector-mongodb-cdc-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-mysql-cdc/3.2.1/flink-sql-connector-mysql-cdc-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-oceanbase-cdc/3.2.1/flink-sql-connector-oceanbase-cdc-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-oracle-cdc/3.2.1/flink-sql-connector-oracle-cdc-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-postgres-cdc/3.2.1/flink-sql-connector-postgres-cdc-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-sqlserver-cdc/3.2.1/flink-sql-connector-sqlserver-cdc-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-tidb-cdc/3.2.1/flink-sql-connector-tidb-cdc-3.2.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-vitess-cdc/3.2.1/flink-sql-connector-vitess-cdc-3.2.1.jar
)

PAIMON_JARS=(
    https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-flink-1.19/0.9.0/paimon-flink-1.19-0.9.0.jar
    https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-flink-action/0.9.0/paimon-flink-action-0.9.0.jar
)

MISC_DRIVERS=(
    https://repo1.maven.org/maven2/mysql/mysql-connector-java/8.0.27/mysql-connector-java-8.0.27.jar
    https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.1/kafka-clients-3.4.1.jar
    https://repo.maven.apache.org/maven2/org/apache/flink/flink-shaded-hadoop-2-uber/2.8.3-10.0/flink-shaded-hadoop-2-uber-2.8.3-10.0.jar
)

function download_all {
    echo "Downloading flink and flink connectors"
    for url in "${FLINK_SQL_CONNECTOR_URLS[@]}"; do
        download_and_extract "$url"
    done

    echo "Downloading flink pipeline connectors"
    for url in "${FLINK_CDC_PIPELINE_CONNECTOR_3_2_1[@]}"; do
        download_and_extract "$url"
    done

    echo "Downloading flink-cdc connectors"
    for url in "${FLINK_SQL_CONNECTOR_CDC_3_2_1[@]}"; do
        download_and_extract "$url"
    done

    echo "Downloading misc drivers"
    for url in "${MISC_DRIVERS[@]}"; do
        download_and_extract "$url"
    done

    echo "Downloading paimon jars"
    for url in "${PAIMON_JARS[@]}"; do
        download_and_extract "$url"
    done

    echo "All downloads and extractions completed"
}

function show_help {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Downloads and extracts Flink connectors and related dependencies.

Options:
    -h, --help      Show this help message and exit

If no options are provided, the script will download and extract all files.
EOF
}

# Parse command line arguments
case "$1" in
    -h|--help)
        show_help
        exit 0
        ;;
    "")
        # No arguments provided, run download_all
        download_all
        ;;
    *)
        echo "Error: Unknown option: $1"
        show_help
        exit 1
        ;;
esac
