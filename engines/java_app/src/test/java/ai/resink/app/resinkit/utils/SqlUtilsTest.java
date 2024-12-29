package ai.resink.app.resinkit.utils;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import java.util.List;


import static ai.resink.app.resinkit.utils.SqlUtils.splitSqlStatements;

class SqlUtilsTest {

    @Test
    public void testSqlSplitter() {
        String sqlScript = "SELECT * FROM table1; " +
                "INSERT INTO table2 VALUES ('value; with semicolon'); " +
                "INSERT INTO table2 VALUES ('another value') RETURNING id; " +
                "-- Comment with a semicolon; \n" +
                "UPDATE table3 SET column = 'value' WHERE id = 1 RETURNING *; " +
                "DELETE FROM table4 WHERE id = 2;";

        List<SqlUtils.SqlStatementInfo> statementsInfo = splitSqlStatements(sqlScript);
        for (SqlUtils.SqlStatementInfo info : statementsInfo) {
            System.out.println(info);
            System.out.println("--------------");
        }
        Assertions.assertEquals(5, statementsInfo.size());
        Assertions.assertEquals("SELECT * FROM table1", statementsInfo.get(0).getStatement());
        Assertions.assertEquals("INSERT INTO table2 VALUES ('value; with semicolon')", statementsInfo.get(1).getStatement());
        Assertions.assertEquals("INSERT INTO table2 VALUES ('another value') RETURNING id", statementsInfo.get(2).getStatement());
        Assertions.assertEquals("-- Comment with a semicolon; \nUPDATE table3 SET column = 'value' WHERE id = 1 RETURNING *", statementsInfo.get(3).getStatement());
        Assertions.assertEquals("DELETE FROM table4 WHERE id = 2", statementsInfo.get(4).getStatement());
        Assertions.assertTrue(statementsInfo.get(0).isReturnsResults());
        Assertions.assertFalse(statementsInfo.get(1).isReturnsResults());
        Assertions.assertTrue(statementsInfo.get(2).isReturnsResults());
        Assertions.assertTrue(statementsInfo.get(3).isReturnsResults());
        Assertions.assertFalse(statementsInfo.get(4).isReturnsResults());
    }

    @Test
    public void testSplitFlinkSql() {
        String sql1 = """
                SET 'sql-client.execution.result-mode' = 'tableau';

                CREATE TABLE Orders (
                    order_number BIGINT,
                    price        DECIMAL(32,2),
                    buyer        ROW<first_name STRING, last_name STRING>,
                    order_time   TIMESTAMP(3)
                ) WITH (
                  'connector' = 'datagen',
                  'number-of-rows' = '100000'
                );

                SELECT buyer, SUM(price) AS total_cost
                FROM Orders
                GROUP BY  buyer
                ORDER BY  total_cost LIMIT 3;
                """;
        List<SqlUtils.SqlStatementInfo> statementsInfo = splitSqlStatements(sql1);
        for (SqlUtils.SqlStatementInfo info : statementsInfo) {
            System.out.println(info);
            System.out.println("--------------");
        }
        Assertions.assertEquals(3, statementsInfo.size());
        Assertions.assertFalse(statementsInfo.get(0).isReturnsResults());
        Assertions.assertFalse(statementsInfo.get(1).isReturnsResults());
        Assertions.assertTrue(statementsInfo.get(2).isReturnsResults());
    }

    @Test
    public void testSplitFlinkSql2() {
        String sql1 = """
                 -- https://nightlies.apache.org/flink/flink-docs-master/docs/dev/table/jdbcdriver/
                 CREATE TABLE T(a INT,b VARCHAR(10)) WITH ('connector' = 'filesystem','path' = 'file:///tmp/T.csv','format' = 'csv');

                 INSERT INTO T VALUES (1, 'Hi'), (2, 'Hello');

                 SELECT * FROM T;

                """;
        List<SqlUtils.SqlStatementInfo> statementsInfo = splitSqlStatements(sql1);
        for (SqlUtils.SqlStatementInfo info : statementsInfo) {
            System.out.println(info);
            System.out.println("--------------");
        }
        Assertions.assertEquals(3, statementsInfo.size());
        Assertions.assertFalse(statementsInfo.get(0).isReturnsResults());
        Assertions.assertFalse(statementsInfo.get(1).isReturnsResults());
        Assertions.assertTrue(statementsInfo.get(2).isReturnsResults());
    }
}