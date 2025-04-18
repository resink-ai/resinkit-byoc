# resinkit-terra

### Components

- flink:1.19.1-scala_2.12-java17
- Paimon
- Flink-CDC
- Kafka

### Ports

- 8081 // Flink web UI
- 8083 // Flink SQL gateway
- 6123 // JobManager's RPC
- 6121-6130 // TaskManagers' data

## Quick Start

### Single docker container

```shell
# build just the docker
make jar resinkit-terra

# some quick test to make sure the container works
make resinkit-terra-test
```

## Integration tests

### Test case: MySQL to Doris

1. `make resinkit-terra-build-mysql2doris`
2. Wait until doris is up, and then:

   1. using doris FE web portal to execute: `create database mydatabase;`
      1. Navigate to http://localhost:8030/Playground/
      2. login with `root` and empty password
      3. run `create database mydatabase;`. ![alt text](../images/doris_create_mydatabase.png)
   2. using CLI:

      ```shell
      docker exec -it resinkit-terra-mysql2doris-doris-1 mysql -h 127.0.0.1 -uroot -P9030 -e 'create database if not exists mydatabase;'
      ```

3. `make resinkit-terra-test-mysql2doris`
4. View Events on Flink
   1. http://localhost:8081/#/job-manager/logs
   2. http://localhost:8081/#/task-manager

### Test case: MySQL to Kafka

1. Repeat the step 1 & 2 from above.
2. Run the tests: `resinkit-terra-test-mysql2kafka`
3. Manual query Kafka: `kcat -C -b localhost:9092 -t mydatabase.User`
4.

### Paimon Test cases

```sql
CREATE CATALOG my_catalog WITH (
    'type'='paimon',
    'warehouse'='file:/tmp/paimon'
);

USE CATALOG my_catalog;

CREATE TABLE MyTable (
  user_id BIGINT,
  item_id BIGINT,
  behavior STRING,
  dt STRING,
  PRIMARY KEY (dt, user_id) NOT ENFORCED
) PARTITIONED BY (dt) WITH (
  'bucket' = '4'
);

SET 'execution.runtime-mode' = 'batch';
SELECT * FROM orders WHERE catalog_id=1025;

SET 'execution.runtime-mode' = 'streaming';
SELECT * FROM MyTable /*+ OPTIONS ('log.scan'='latest') */;

ALTER TABLE my_table SET ('bucket' = '4');
INSERT OVERWRITE my_table PARTITION (dt = '2022-01-01');
```
