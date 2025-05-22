
# Flink Related Tasks

All the flink related tasks have the following common base structure

```yaml
task_type: string                # Type identifier
name: string                     # Human-readable task name
description: string              # Optional description
task_timeout_seconds: integer    # Task timeout

resources:                       # Standardized resources section, contains keyed objects
  flink_jars:                    # (Optional) All JAR dependencies in one place
    - name: string               # Human-readable name
      type: string               # Either "classpath" or "lib" 
      source: string             # "download", "upload", "reference"
      location: string           # URL or file reference
      

```
