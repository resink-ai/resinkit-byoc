// (C)2024 resink.ai
package ai.resink.app.resinkit.controllers;

import ai.resink.app.resinkit.models.SqlExecResult;
import ai.resink.app.resinkit.services.FlinkSqlExecutionService;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.exception.ExceptionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;

import static java.nio.file.StandardCopyOption.REPLACE_EXISTING;

@Slf4j
@RestController
@RequestMapping("/api/v0/flink")
@Tag(name = "Flink", description = "Flink SQL API")
public class FlinkController {

    private static final Map<String, String> NAME_TO_URL_MAP = Map.ofEntries(
            Map.entry("flink-cdc-pipeline-connector-mysql-3.2.0", "https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-mysql/3.2.0/flink-cdc-pipeline-connector-mysql-3.2.0.jar"),
            Map.entry("flink-cdc-pipeline-connector-doris-3.2.0", "https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-doris/3.2.0/flink-cdc-pipeline-connector-doris-3.2.0.jar"),
            Map.entry("flink-cdc-pipeline-connector-starrocks-3.2.0", "https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-starrocks/3.2.0/flink-cdc-pipeline-connector-starrocks-3.2.0.jar"),
            Map.entry("flink-cdc-pipeline-connector-kafka-3.2.0", "https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-kafka/3.2.0/flink-cdc-pipeline-connector-kafka-3.2.0.jar"),
            Map.entry("flink-cdc-pipeline-connector-paimon-3.2.0", "https://repo1.maven.org/maven2/org/apache/flink/flink-cdc-pipeline-connector-paimon/3.2.0/flink-cdc-pipeline-connector-paimon-3.2.0.jar"),
            Map.entry("flink-sql-connector-db2-cdc-3.2.0", "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-db2-cdc/3.2.0/flink-sql-connector-db2-cdc-3.2.0.jar"),
            Map.entry("flink-sql-connector-mongodb-cdc-3.2.0", "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-mongodb-cdc/3.2.0/flink-sql-connector-mongodb-cdc-3.2.0.jar"),
            Map.entry("flink-sql-connector-mysql-cdc-3.2.0", "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-mysql-cdc/3.2.0/flink-sql-connector-mysql-cdc-3.2.0.jar"),
            Map.entry("flink-sql-connector-oceanbase-cdc-3.2.0", "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-oceanbase-cdc/3.2.0/flink-sql-connector-oceanbase-cdc-3.2.0.jar"),
            Map.entry("flink-sql-connector-oracle-cdc-3.2.0", "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-oracle-cdc/3.2.0/flink-sql-connector-oracle-cdc-3.2.0.jar"),
            Map.entry("flink-sql-connector-postgres-cdc-3.2.0", "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-postgres-cdc/3.2.0/flink-sql-connector-postgres-cdc-3.2.0.jar"),
            Map.entry("flink-sql-connector-sqlserver-cdc-3.2.0", "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-sqlserver-cdc/3.2.0/flink-sql-connector-sqlserver-cdc-3.2.0.jar"),
            Map.entry("flink-sql-connector-tidb-cdc-3.2.0", "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-tidb-cdc/3.2.0/flink-sql-connector-tidb-cdc-3.2.0.jar"),
            Map.entry("flink-sql-connector-vitess-cdc-3.2.0", "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-vitess-cdc/3.2.0/flink-sql-connector-vitess-cdc-3.2.0.jar")
    );

    private final RestClient restClient;

    @Value("${flink.home:/opt/flink}")
    private String flinkHome;

    @Autowired
    private FlinkSqlExecutionService flinkSqlService;

    public FlinkController(RestClient.Builder restClientBuilder) {
        this.restClient = restClientBuilder.build();
    }

    @PutMapping("/lib/download")
    public ResponseEntity<String> downloadLib(@RequestBody Map<String, String> request) {
        String name = request.get("name");
        String url = request.get("url");
        String msg = "Downloading package: " + name + ", url: " + url;

        if (url == null && name != null) {
            url = NAME_TO_URL_MAP.get(name);
            if (url == null) {
                return ResponseEntity.badRequest().body("Invalid package name: " + name);
            }
        }

        if (url == null) {
            return ResponseEntity.badRequest().body("URL is required");
        }

        try {
            String fileName = url.substring(url.lastIndexOf('/') + 1);
            File targetFile = new File(flinkHome + "/lib/" + fileName);

            Resource resource = restClient.get()
                    .uri(url)
                    .retrieve()
                    .body(Resource.class);

            if (resource != null) {
                Files.copy(resource.getInputStream(), targetFile.toPath(), REPLACE_EXISTING);
                return ResponseEntity.ok(msg + " successfully");
            } else {
                return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Error downloading file: Resource is null");
            }
        } catch (IOException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Error " + msg + e.getMessage());
        }
    }

    @PostMapping("/lib/upload")
    public ResponseEntity<String> uploadLib(@RequestParam("file") MultipartFile file) {
        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body("Please select a file to upload");
        }

        try {
            byte[] bytes = file.getBytes();
            String fileName = file.getOriginalFilename();
            Files.write(Paths.get(flinkHome + "/lib/" + fileName), bytes);

            return ResponseEntity.ok("File uploaded successfully");
        } catch (IOException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Error uploading file: " + e.getMessage());
        }
    }

    @PostMapping(value = "/runsql", consumes = {MediaType.TEXT_PLAIN_VALUE, MediaType.APPLICATION_JSON_VALUE})
    public ResponseEntity<?> runSql(@RequestBody String sql) {
        if (sql == null || sql.isEmpty()) {
            return ResponseEntity.badRequest().body("SQL statement is required");
        }
        try {
            List<SqlExecResult> allResults = flinkSqlService.executeSql(sql);
            return ResponseEntity.ok(allResults);
        } catch (Exception e) {
            String msg = ExceptionUtils.getRootCauseMessage(e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Error executing: \n " + sql + "\nError:" + msg);
        }
    }
}