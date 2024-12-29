# Service Operations

## Quick Start



# MySQL to Kafka

1. `make jar build-mysql2kafka`
2. Wait until docker containers up fully up and running, test if Kafka is running with `kcat -b localhost:9092 -L`
3. Add some test data and kick off the job:
   - `make test-mysql2kafka`
4. Connect to kafka and view the messages:
   - `kcat -C -b localhost:9092 -t mydatabase.User` or
   - `kcat -b localhost:9092 -G my_consumer -o earliest '^mydatabase.*'`
5. Add more data: 
   - `docker exec -it resinkit-testmysql-mysql-1 python /usr/local/bin/generate_data.py`


# MySQL to Kafka to Flink SQL

1. open sql-client.sh: `sql-client.sh --jar flink-connector-kafka-3.3.0-1.19.jar --jar kafka-clients-3.4.0.jar`
2. Execute the following:

```sql
CREATE TABLE mydatabase_User (
  `event_time` TIMESTAMP_LTZ(3) METADATA FROM 'value.source.timestamp' VIRTUAL,  -- from Debezium format
  `origin_table` STRING METADATA FROM 'value.source.table' VIRTUAL, -- from Debezium format
  `partition_id` BIGINT METADATA FROM 'partition' VIRTUAL,  -- from Kafka connector
  `offset` BIGINT METADATA VIRTUAL,  -- from Kafka connector
  `id` STRING,
  `name` STRING,
  `email` STRING,
  `email_verified` TIMESTAMP_LTZ(3),
  `image` STRING,
  `invalid_login_attempts` INT,
  `locked_at` TIMESTAMP_LTZ(3),
  `password` STRING,
  `created_at` TIMESTAMP_LTZ(3),
  `updated_at` TIMESTAMP_LTZ(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'mydatabase.User',
    'properties.bootstrap.servers' = 'localhost:9092',
    'properties.group.id' = 'mydatabase_user_consumer_group',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'debezium-json'
);


select * from mydatabase_User;
```

# BYOC NGROK 

```shell 
# 1. install ngrok, see https://ngrok.com/docs/getting-started/#step-5-secure-your-app

# 2. open a tunnel (one port per account)
ngrok http http://localhost:8000
NG_HOST=c47b-4-14-32-22.ngrok-free.app

# 3. verify the connectivity
curl -H "Content-Type: application/json" https://$NG_HOST/api-docs
curl https://$NG_HOST/hello

# test flink-sql connectivity
curl -X POST https://$NG_HOST/api/v0/flink/runsql \
     -H "Content-Type: text/plain" \
     -d "select 1"

```
