# Config Spec: 'flink_sql'

## Summary

```YAML
task_type: string                  # Type identifier for the task. Must be "flink_sql".
name: string                       # Human-readable name for the task. This is mandatory.
description: string                # (Optional) A more detailed description of the task. Defaults to an empty string.
task_timeout_seconds: integer      # (Optional) Maximum duration in seconds the task is allowed to run. Defaults to 3600.

job:
  sql: string                      # The SQL script to be executed by Flink. Can contain multiple statements.
  pipeline:
    name: string                   # (Optional) Name of the Flink pipeline. Defaults to the top-level 'name' of the task.
    parallelism: integer           # (Optional) Default parallelism for the Flink job. Defaults to 1.

resources:                         # (Optional) Standardized resources section.
  flink_jars:                      # (Optional) List of JAR dependencies for the Flink job.
    - name: string                 # Human-readable name for the JAR.
      type: string                 # Type of JAR. Expected values: "classpath", "lib".
      source: string               # Source of the JAR. Expected values: "download", "upload", "reference".
      location: string             # URL or file reference/path for the JAR.
  flink_cdc_jars:                  # (Optional) List of JAR dependencies for the Flink CDC job.
    - name: string                 # Human-readable name for the JAR.
      type: string                 # Type of JAR. Expected values: "classpath", "lib".
      source: string               # Source of the JAR. Expected values: "download", "upload", "reference".
      location: string             # URL or file reference/path for the JAR.
# Add other potential resource types under 'resources' as needed.
```
