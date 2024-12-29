use default_database;

CREATE TABLE T(a INT,b VARCHAR(10)) WITH ('connector' = 'filesystem','path' = 'file:///tmp/T.csv','format' = 'csv');
INSERT INTO T VALUES (1, 'Hi'), (2, 'Hello');
SELECT * FROM T;

--------------------------------------------------------------------------------------------------------------
-- Materialized Table
-- https://nightlies.apache.org/flink/flink-docs-master/docs/dev/table/materialized-table/quickstart/
--------------------------------------------------------------------------------------------------------------

-- ENV CATALOG_STORE_PATH=/tmp/flink/catalog-store
-- ENV CATALOG_PATH=/tmp/flink/catalog
-- ENV DEFAULT_DB_PATH=/tmp/flink/mydb
-- ENV CHECKPOINTS_PATH=/tmp/flink/checkpoints
-- ENV SAVEPOINTS_PATH=/tmp/flink/savepoints
-- RUN mkdir -p $CATALOG_STORE_PATH $CATALOG_PATH $DEFAULT_DB_PATH $CHECKPOINTS_PATH $SAVEPOINTS_PATH

CREATE CATALOG mt_cat WITH (
    'type' = 'filesystem',
    'path' = 'file:///tmp/flink/catalog',
    'default-database' = 'mydb'
);

USE CATALOG mt_cat;

-- 1. Create Source table and specify the data format is json
CREATE TABLE json_source (
    order_id BIGINT,
    user_id BIGINT,
    user_name STRING,
    order_created_at STRING,
    payment_amount_cents BIGINT
) WITH (
    'format' = 'json',
    'source.monitor-interval' = '10s'
);
-- 2. Insert some test data
INSERT INTO json_source
VALUES (1001, 1, 'user1', '2024-06-19', 10),
    (1002, 2, 'user2', '2024-06-19', 20),
    (1003, 3, 'user3', '2024-06-19', 30),
    (1004, 4, 'user4', '2024-06-19', 40),
    (1005, 1, 'user1', '2024-06-20', 10),
    (1006, 2, 'user2', '2024-06-20', 20),
    (1007, 3, 'user3', '2024-06-20', 30),
    (1008, 4, 'user4', '2024-06-20', 40);