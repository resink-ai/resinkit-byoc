package ai.resink.app.resinkit.services;

import ai.resink.app.resinkit.models.SqlExecResult;
import ai.resink.app.resinkit.utils.SqlUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
public class FlinkSqlExecutionService {

    @Autowired
    @Qualifier("flinkDataSource")
    private DataSource flinkDataSource;

    public List<SqlExecResult> executeSql(String sql) throws SQLException {
        List<SqlExecResult> allResults = new ArrayList<>();
        List<SqlUtils.SqlStatementInfo> sqlStatements = SqlUtils.splitSqlStatements(sql);

        try (Connection connection = flinkDataSource.getConnection();
             Statement statement = connection.createStatement()) {
            for (SqlUtils.SqlStatementInfo sqlInfo : sqlStatements) {
                String sqli = sqlInfo.getStatement();
                boolean hasResultSet = statement.execute(sqli);
                if (hasResultSet) {
                    try (ResultSet rs = statement.getResultSet()) {
                        allResults.add(processResultSet(sqli, rs));
                    }
                } else {
                    int updateCount = statement.getUpdateCount();
                    allResults.add(new SqlExecResult(sqli, List.of(), List.of(), updateCount));
                }
            }
        }
        return allResults;
    }

    private SqlExecResult processResultSet(String sql, ResultSet rs) throws SQLException {
        ResultSetMetaData metaData = rs.getMetaData();
        int columnCount = metaData.getColumnCount();
        List<String> headers = new ArrayList<>();
        for (int i = 1; i <= columnCount; i++) {
            headers.add(metaData.getColumnName(i));
        }
        List<List<Object>> rows = new ArrayList<>();
        while (rs.next()) {
            List<Object> row = new ArrayList<>();
            for (int i = 1; i <= columnCount; i++) {
                Object value = rs.getObject(i);
                row.add(value);
            }
            rows.add(row);
        }
        return new SqlExecResult(sql, headers, rows, -1);
    }
}
