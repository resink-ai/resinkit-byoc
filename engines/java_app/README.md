## Resinkit Service Testing Commands

```shell
# test endpoint
curl localhost:8000/hello

# test flink-sql connectivity
curl -X POST http://localhost:8000/api/v0/flink/runsql \
     -H "Content-Type: text/plain" \
     -d "select 1"

# test sample flink SQL
curl -X POST -H "Content-Type: text/plain" http://localhost:9081/api/v0/flink/runsql \
    -d "CREATE TABLE T(a INT, b VARCHAR(10)) WITH ('connector' = 'filesystem', 'path' = 'file:///tmp/T.csv', 'format' = 'csv'); INSERT INTO T VALUES (1, 'Hi'), (2, 'Hello');" | jq .

# test run SQL file
curl -X POST -H "Content-Type: text/plain" http://localhost:9081/api/v0/flink/runsql --data-binary @docker/flink/flink_sql_1.sql
```

#### Download jar

```shell
# Download with name and URL
curl -X PUT -H "Content-Type: application/json" localhost:8000/api/v0/flink/lib/download -d '{"name": "flink-cdc-pipeline-connector-mysql-3.2.0", "url": "https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-mysql/3.2.0/flink-cdc-pipeline-connector-mysql-3.2.0.jar"}'

# Download with just name
curl -X PUT -H "Content-Type: application/json" localhost:8000/api/v0/flink/lib/download -d '{"name": "flink-cdc-pipeline-connector-kafka-3.2.0"}'
```

#### Test MySQL connection

```shell
curl -X POST "http://localhost:8000/mysql/test-connection" -H "Content-Type: application/json" -d '{
  "hostname": "mysql",
  "port": "3306",
  "username": "root",
  "password": "rootpassword"
}'
```

#### Swagger
http://localhost:8000/swagger-ui/index.html

#### Flink CDC in sql-client.sh

```shell

CREATE TABLE user_cdc (
    `id` STRING,
    `name` STRING,
    `email` STRING,
    `emailVerified` TIMESTAMP(3),
    `password` STRING,
    `image` STRING,
    `createdAt` TIMESTAMP(3),
    `updatedAt` TIMESTAMP(3),
    `invalid_login_attempts` INT,
    `lockedAt` TIMESTAMP(3),
    PRIMARY KEY(`id`) NOT ENFORCED
) WITH (
    'connector' = 'mysql-cdc',
    'hostname' = 'mysql',
    'port' = '3306',
    'username' = 'root',
    'password' = 'rootpassword',
    'database-name' = 'mydatabase',
    'table-name' = 'User'
);

SELECT * FROM user_cdc;
```
