package ai.resink.app.resinkit.models;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;

@Data
@AllArgsConstructor
public class SqlExecResult {
    String sql;
    List<String> headers;
    List<List<Object>> rows;
    /**
     * Update count, -1 if return result set, otherwise return the update count.
     */
    Integer updateCount;
}
