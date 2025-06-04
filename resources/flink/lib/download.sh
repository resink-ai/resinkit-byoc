#!/bin/bash
# shellcheck disable=SC2206

set -eo pipefail

download_and_extract() {
    url="$1"
    filename="$(basename "$url")"

    # Check if file already exists
    if [ -f "$filename" ]; then
        echo "File $filename already exists, skipping download"
        return 0
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
    *.tar.gz | *.tgz)
        tar -xzf "$filename"
        ;;
    *.tar.bz2 | *.tbz2)
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
    *.jar)
        echo "File $filename is a jar file, skipping extraction"
        return 0
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

    # Return the full path of the extracted file
    echo "$(readlink -f "$filename")"
}

########################################################
FLINK_CDC_VER=3.4.0
PAIMON_VER=1.1.1
FLINK_VER_MAJOR=1.19
FLINK_VER_MINOR=1.19.2
########################################################

# See: https://flink.apache.org/downloads/
# Regular Connector JARs (flink-connector-*):
# - Primarily used as dependencies in Flink **applications**
# - For standalone applications, include them in your application's JAR dependencies
FLINK_CONNECTOR_URLS=(
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-aws-kinesis-firehose/5.0.0-$FLINK_VER_MAJOR/flink-connector-aws-kinesis-firehose-5.0.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-aws-kinesis-streams/5.0.0-$FLINK_VER_MAJOR/flink-connector-aws-kinesis-streams-5.0.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-kinesis/5.0.0-$FLINK_VER_MAJOR/flink-connector-kinesis-5.0.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-dynamodb/5.0.0-$FLINK_VER_MAJOR/flink-connector-dynamodb-5.0.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-sqs/5.0.0-$FLINK_VER_MAJOR/flink-connector-sqs-5.0.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-cassandra_2.12/3.2.0-$FLINK_VER_MAJOR/flink-connector-cassandra_2.12-3.2.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-gcp-pubsub/3.1.0-$FLINK_VER_MAJOR/flink-connector-gcp-pubsub-3.1.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-hbase-base/4.0.0-$FLINK_VER_MAJOR/flink-connector-hbase-base-4.0.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-jdbc/3.2.0-$FLINK_VER_MAJOR/flink-connector-jdbc-3.2.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-kafka/3.3.0-$FLINK_VER_MAJOR/flink-connector-kafka-3.3.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-mongodb/1.2.0-$FLINK_VER_MAJOR/flink-connector-mongodb-1.2.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-opensearch2/2.0.0-$FLINK_VER_MAJOR/flink-connector-opensearch2-2.0.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-prometheus/1.0.0-$FLINK_VER_MAJOR/flink-connector-prometheus-1.0.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-pulsar/4.1.0-1.18/flink-connector-pulsar-4.1.0-1.18.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-files/$FLINK_VER_MINOR/flink-connector-files-$FLINK_VER_MINOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-datagen/$FLINK_VER_MINOR/flink-connector-datagen-$FLINK_VER_MINOR.jar
)

# SQL Connector JARs (flink-sql-connector-*):
# - Should be placed in /opt/flink/lib directory
# - Enable SQL statements to interact with external systems
# - Needed for Flink SQL Client, SQL Gateway, and SQL API usage
FLINK_SQL_CONNECTOR_URLS=(
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-dynamodb/5.0.0-$FLINK_VER_MAJOR/flink-sql-connector-dynamodb-5.0.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-aws-kinesis-firehose/5.0.0-$FLINK_VER_MAJOR/flink-sql-connector-aws-kinesis-firehose-5.0.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-aws-kinesis-streams/5.0.0-$FLINK_VER_MAJOR/flink-sql-connector-aws-kinesis-streams-5.0.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kinesis/4.3.0-$FLINK_VER_MAJOR/flink-sql-connector-kinesis-4.3.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-elasticsearch6_2.12/1.9.1/flink-sql-connector-elasticsearch6_2.12-1.9.1.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-hbase-2.2/4.0.0-$FLINK_VER_MAJOR/flink-sql-connector-hbase-2.2-4.0.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-hive-3.1.3_2.12/$FLINK_VER_MINOR/flink-sql-connector-hive-3.1.3_2.12-$FLINK_VER_MINOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.3.0-$FLINK_VER_MAJOR/flink-sql-connector-kafka-3.3.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-mongodb/1.2.0-$FLINK_VER_MAJOR/flink-sql-connector-mongodb-1.2.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-opensearch/1.2.0-$FLINK_VER_MAJOR/flink-sql-connector-opensearch-1.2.0-$FLINK_VER_MAJOR.jar
)

# https://github.com/apache/flink-cdc/releases/tag/release-$FLINK_CDC_VER
FLINK_CDC_PIPELINE_CONNECTOR_3_2_1=(
    https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-mysql/$FLINK_CDC_VER/flink-cdc-pipeline-connector-mysql-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-doris/$FLINK_CDC_VER/flink-cdc-pipeline-connector-doris-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-starrocks/$FLINK_CDC_VER/flink-cdc-pipeline-connector-starrocks-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-kafka/$FLINK_CDC_VER/flink-cdc-pipeline-connector-kafka-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-paimon/$FLINK_CDC_VER/flink-cdc-pipeline-connector-paimon-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-elasticsearch/$FLINK_CDC_VER/flink-cdc-pipeline-connector-elasticsearch-$FLINK_CDC_VER.jar
)

FLINK_CONNECTOR_CDC_3_2_1=(
    # https://repo1.maven.org/maven2/org/apache/flink/flink-connector-debezium/$FLINK_CDC_VER/flink-connector-debezium-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-db2-cdc/$FLINK_CDC_VER/flink-connector-db2-cdc-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-mongodb-cdc/$FLINK_CDC_VER/flink-connector-mongodb-cdc-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-mysql-cdc/$FLINK_CDC_VER/flink-connector-mysql-cdc-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-oracle-cdc/$FLINK_CDC_VER/flink-connector-oracle-cdc-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-postgres-cdc/$FLINK_CDC_VER/flink-connector-postgres-cdc-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-sqlserver-cdc/$FLINK_CDC_VER/flink-connector-sqlserver-cdc-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-tidb-cdc/$FLINK_CDC_VER/flink-connector-tidb-cdc-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-connector-oceanbase-cdc/$FLINK_CDC_VER/flink-connector-oceanbase-cdc-$FLINK_CDC_VER.jar
)

FLINK_SQL_CONNECTOR_CDC_3_2_1=(
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-db2-cdc/$FLINK_CDC_VER/flink-sql-connector-db2-cdc-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-mongodb-cdc/$FLINK_CDC_VER/flink-sql-connector-mongodb-cdc-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-mysql-cdc/$FLINK_CDC_VER/flink-sql-connector-mysql-cdc-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-oceanbase-cdc/$FLINK_CDC_VER/flink-sql-connector-oceanbase-cdc-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-oracle-cdc/$FLINK_CDC_VER/flink-sql-connector-oracle-cdc-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-postgres-cdc/$FLINK_CDC_VER/flink-sql-connector-postgres-cdc-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-sqlserver-cdc/$FLINK_CDC_VER/flink-sql-connector-sqlserver-cdc-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-tidb-cdc/$FLINK_CDC_VER/flink-sql-connector-tidb-cdc-$FLINK_CDC_VER.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-vitess-cdc/$FLINK_CDC_VER/flink-sql-connector-vitess-cdc-$FLINK_CDC_VER.jar
)

# PAIMON $PAIMON_VER
PAIMON_JARS=(
    https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-flink-$FLINK_VER_MAJOR/$PAIMON_VER/paimon-flink-$FLINK_VER_MAJOR-$PAIMON_VER.jar
    https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-flink-action/$PAIMON_VER/paimon-flink-action-$PAIMON_VER.jar
    https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-s3/$PAIMON_VER/paimon-s3-$PAIMON_VER.jar
    https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-azure/$PAIMON_VER/paimon-azure-$PAIMON_VER.jar
    https://repo.maven.apache.org/maven2/org/apache/paimon/paimon-gs/$PAIMON_VER/paimon-gs-$PAIMON_VER.jar
)

# https://nightlies.apache.org/flink/flink-docs-release-$FLINK_VER_MAJOR/docs/connectors/table/jdbc/#dependencies
FLINK_JDBC_SQL_CONNECTORS=(
    https://jdbc.postgresql.org/download/postgresql-42.7.5.jar
    https://repo.maven.apache.org/maven2/org/apache/flink/flink-connector-jdbc/3.2.0-$FLINK_VER_MAJOR/flink-connector-jdbc-3.2.0-$FLINK_VER_MAJOR.jar
    https://repo1.maven.org/maven2/mysql/mysql-connector-java/8.0.27/mysql-connector-java-8.0.27.jar
    https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.4.1/kafka-clients-3.4.1.jar
)

# Needed for access object storage
FLINK_FILES_JARS=(
    https://repo.maven.apache.org/maven2/org/apache/flink/flink-shaded-hadoop-2-uber/2.8.3-10.0/flink-shaded-hadoop-2-uber-2.8.3-10.0.jar
    https://repo1.maven.org/maven2/org/apache/flink/flink-s3-fs-hadoop/$FLINK_VER_MINOR/flink-s3-fs-hadoop-$FLINK_VER_MINOR.jar
)

# Note:
#   - sql connectors are needed for SQL Gateway which is started as flink sql gateway service
#   - jar connectors can be added when running flink standalone application (aka we can download then on the fly)
function download_all {
    echo "Downloading flink and flink connectors"
    for url in "${FLINK_SQL_CONNECTOR_URLS[@]}"; do
        download_and_extract "$url"
    done

    echo "Downloading misc drivers"
    for url in "${FLINK_JDBC_SQL_CONNECTORS[@]}"; do
        download_and_extract "$url"
    done

    echo "Downloading paimon jars"
    for url in "${PAIMON_JARS[@]}"; do
        download_and_extract "$url"
    done

    echo "Downloading flink files jars"
    for url in "${FLINK_FILES_JARS[@]}"; do
        download_and_extract "$url"
    done

    mkdir -p cdc
    (
        cd cdc
        echo "Downloading flink pipeline connectors"
        for url in "${FLINK_CDC_PIPELINE_CONNECTOR_3_2_1[@]}"; do
            download_and_extract "$url"
        done

        echo "Downloading flink-cdc connectors"
        for url in "${FLINK_SQL_CONNECTOR_CDC_3_2_1[@]}"; do
            download_and_extract "$url"
        done
    )

    echo "All downloads and extractions completed"
}

function show_help {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Downloads and extracts Flink connectors and related dependencies.

Options:
    -h, --help      Show this help message and exit

If no options are provided, the script will download and extract all files.
EOF
}

# Parse command line arguments
case "$1" in
-h | --help)
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
