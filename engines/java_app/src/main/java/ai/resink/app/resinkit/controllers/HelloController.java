package ai.resink.app.resinkit.controllers;

import lombok.extern.log4j.Log4j2;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.SimpleDriverDataSource;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import javax.sql.DataSource;
import java.sql.Driver;
import java.util.Map;

@Log4j2
@RestController
public class HelloController {

    @GetMapping("/hello")
    public String index() {
        return "Greetings from Spring Boot!";
    }

    /**
     * Test a MySQL connection using the provided connection parameters.
     * Sample CURL request:
     * <pre>
     *  curl -X POST "http://localhost:8080/mysql/test-connection" -H "Content-Type: application/json" -d '{
     *    "hostname": "127.0.0.1",
     *    "port": "3306",
     *    "username": "root",
     *    "password": "rootpassword"
     *  }'
     *
     * @param connectionParams
     * @return
     */
    @PostMapping("/mysql/test-connection")
    public ResponseEntity<String> testConnection(@RequestBody Map<String, String> connectionParams) {
        String hostname = connectionParams.get("hostname");
        String port = connectionParams.get("port");
        String username = connectionParams.get("username");
        String password = connectionParams.get("password");

        // Construct the JDBC URL
        String jdbcUrl = String.format("jdbc:mysql://%s:%s/", hostname, port);

        try {
            // Explicitly load the MySQL driver
            Class<?> driverClass = Class.forName("com.mysql.cj.jdbc.Driver");
            Driver driver = (Driver) driverClass.getDeclaredConstructor().newInstance();

            // Create a DataSource with the explicit driver
            DataSource dataSource = new SimpleDriverDataSource(driver, jdbcUrl, username, password);

            // Create a JdbcTemplate
            JdbcTemplate jdbcTemplate = new JdbcTemplate(dataSource);

            // Execute the query
            Integer result = jdbcTemplate.queryForObject("SELECT 1", Integer.class);

            if (result != null && result == 1) {
                return ResponseEntity.ok("Connection successful. Query returned: " + result);
            } else {
                return ResponseEntity.ok("Connection successful, but unexpected result: " + result);
            }
        } catch (Exception e) {
            log.error("Connection failed", e);
            return ResponseEntity.badRequest().body("Connection failed: " + e.getMessage());
        }
    }

}
