package ai.resink.app.resinkit.utils;

import lombok.Value;

import java.util.ArrayList;
import java.util.List;

public class SqlUtils {
    public static List<SqlStatementInfo> splitSqlStatements(String multipleSqlStatements) {
        List<SqlStatementInfo> result = new ArrayList<>();
        List<String> statements = splitSqlScript(multipleSqlStatements);

        for (String statement : statements) {
            boolean returnsResults = checkIfReturnsResults(statement);
            result.add(new SqlStatementInfo(statement.trim(), returnsResults));
        }

        return result;
    }

    static List<String> splitSqlScript(String script) {
        List<String> statements = new ArrayList<>();
        StringBuilder sb = new StringBuilder();
        boolean inSingleQuote = false;
        boolean inDoubleQuote = false;
        boolean inBackQuote = false;
        boolean inLineComment = false;
        boolean inBlockComment = false;
        int length = script.length();

        for (int i = 0; i < length; i++) {
            char c = script.charAt(i);
            char next = i + 1 < length ? script.charAt(i + 1) : '\0';

            if (inLineComment) {
                sb.append(c);
                if (c == '\n') {
                    inLineComment = false;
                }
            } else if (inBlockComment) {
                sb.append(c);
                if (c == '*' && next == '/') {
                    sb.append(next);
                    i++;
                    inBlockComment = false;
                }
            } else if (inSingleQuote) {
                sb.append(c);
                if (c == '\\' && next == '\'') {
                    sb.append(next);
                    i++;
                } else if (c == '\'') {
                    inSingleQuote = false;
                }
            } else if (inDoubleQuote) {
                sb.append(c);
                if (c == '\\' && next == '"') {
                    sb.append(next);
                    i++;
                } else if (c == '"') {
                    inDoubleQuote = false;
                }
            } else if (inBackQuote) {
                sb.append(c);
                if (c == '`') {
                    inBackQuote = false;
                }
            } else {
                if (c == '-' && next == '-') {
                    sb.append(c);
                    sb.append(next);
                    i++;
                    inLineComment = true;
                } else if (c == '/' && next == '*') {
                    sb.append(c);
                    sb.append(next);
                    i++;
                    inBlockComment = true;
                } else if (c == '\'') {
                    sb.append(c);
                    inSingleQuote = true;
                } else if (c == '"') {
                    sb.append(c);
                    inDoubleQuote = true;
                } else if (c == '`') {
                    sb.append(c);
                    inBackQuote = true;
                } else if (c == ';') {
                    // End of statement
                    String statement = sb.toString().trim();
                    if (!statement.isEmpty()) {
                        statements.add(statement);
                    }
                    sb.setLength(0);
                } else {
                    sb.append(c);
                }
            }
        }

        // Add the last statement if any
        String remaining = sb.toString().trim();
        if (!remaining.isEmpty()) {
            statements.add(remaining);
        }

        return statements;
    }

    private static boolean checkIfReturnsResults(String statement) {
        String upperStatement = statement.toUpperCase().trim();
        return upperStatement.startsWith("SELECT") ||
                upperStatement.startsWith("SHOW") ||
                upperStatement.startsWith("DESCRIBE") ||
                upperStatement.startsWith("EXPLAIN") ||
                (upperStatement.contains("INSERT") && upperStatement.contains("RETURNING")) ||
                (upperStatement.contains("UPDATE") && upperStatement.contains("RETURNING")) ||
                (upperStatement.contains("DELETE") && upperStatement.contains("RETURNING"));
    }

    @Value
    public static class SqlStatementInfo {
        String statement;
        boolean returnsResults;
    }
}
