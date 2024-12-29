-- https://nightlies.apache.org/flink/flink-docs-master/docs/dev/table/jdbcdriver/
CREATE TABLE T(a INT,b VARCHAR(10)) WITH ('connector' = 'filesystem','path' = 'file:///tmp/T.csv','format' = 'csv');

INSERT INTO T VALUES (1, 'Hi'), (2, 'Hello');

SELECT * FROM T;
