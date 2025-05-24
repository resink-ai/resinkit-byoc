#!/bin/bash

# Inspect Kafka using kcat
function inspect_kafka() {
    echo "================================================"
    echo "Kafka:"
    kcat -L -b localhost:9092 | grep -E '^(Metadata|Broker|Topic|Partition|Leader|Replicas|Isr)'
    echo " Producing some sample messages to kafka topic topic_test_transactions"
    # Sending some sample messages to kafka
    kcat -P -b localhost:9092 -t topic_test_transactions -p 0 <<EOF
{ "transaction_id": "txn123", "sender_id": 101, "recipient_id": 201, "amount": 100.0, "timestamp": "2024-05-06T08:30:00Z", "note": "Payment for services", "transaction_type": "debit", "transaction_status": "completed", "fee": 1.0 }
{ "transaction_id": "txn456", "sender_id": 102, "recipient_id": 202, "amount": 150.0, "timestamp": "2024-05-06T09:45:00Z", "note": "Refund for overcharge", "transaction_type": "credit", "transaction_status": "completed", "fee": 1.5 }
{ "transaction_id": "txn789", "sender_id": 103, "recipient_id": 203, "amount": 200.0, "timestamp": "2024-05-06T11:15:00Z", "note": "Transfer to savings account", "transaction_type": "debit", "transaction_status": "pending", "fee": 2.0 }
EOF
    echo " Consuming messages from kafka topic topic_test_transactions"
    kcat -C -b localhost:9092 -t topic_test_transactions -p 0 -e
    echo "================================================"
    echo " Inspecting kafka topics"
    kafka-topics --bootstrap-server localhost:9092 --list
    echo "================================================"
    echo " Inspecting kafka topic topic_test_transactions"
    kafka-topics --bootstrap-server localhost:9092 --describe --topic topic_test_transactions
    echo "================================================"
    echo " Inspecting kafka topic topic_test_transactions"
    kafka-topics --bootstrap-server localhost:9092 --describe --topic topic_test_transactions
}

function inspect_flink() {
    echo "================================================"
    echo "Flink Job Manager:"
    curl -s http://localhost:8081/config | jq .
    echo "Flink Job Manager Jobs:"
    curl -s http://localhost:8081/jobs/overview | jq .

    echo "================================================"
    echo "Flink SQL Gateway:"
    curl -s http://localhost:8083/info | jq .
    echo "================================================"
}

function inspect_minio() {
    MINIO_MC_BIN="/opt/minio/bin/mc"
    MINIO_ENDPOINT="http://127.0.0.1:9000"
    MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-admin}"
    MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-minio123}"
    echo "================================================"
    echo "Minio:"
    "$MINIO_MC_BIN" alias set localminio "$MINIO_ENDPOINT" "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"
    echo "================================================"
    echo "Minio Buckets:"
    "$MINIO_MC_BIN" ls localminio
    echo "================================================"
    echo "Minio create bucket test-bucket:"
    "$MINIO_MC_BIN" mb localminio/test-bucket
    echo "================================================"
    echo "Minio upload file to bucket test-bucket:"
    "$MINIO_MC_BIN" cp $MINIO_MC_BIN localminio/test-bucket/mc
    echo "================================================"
    echo "Minio list bucket test-bucket:"
    "$MINIO_MC_BIN" ls localminio/test-bucket
    echo "================================================"
}

function inspect_mariadb() {
    echo "================================================"
    echo "Mariadb status:"
    service mariadb status
    echo "================================================"
    echo "Mariadb version:"
    mysql -u root -p -e "SHOW VARIABLES LIKE 'log_bin';"
    echo "Mariadb version:"
    mysql -u root -p -e "SELECT VERSION();"
    echo "Mariadb show databases:"
    mysql -u root -p -e "SHOW DATABASES;"
    echo "Mariadb show tables:"
    echo "================================================"
}
