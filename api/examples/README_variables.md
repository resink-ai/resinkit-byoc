# Using Variables in Resinkit

Variables allow you to store sensitive or configuration values securely and use them in your Flink job definitions.

## Features

- **Encrypted Storage**: Variable values are encrypted before being stored in the database
- **Write-Only**: Once saved, variable values are not visible through the API
- **Simple Templating**: Use `${VARIABLE_NAME}` syntax in your YAML configurations
- **Automatic Resolution**: Variables are automatically resolved when submitting jobs

## Managing Variables

### Create a Variable

```bash
curl -X POST "http://localhost:8000/api/agent/variables" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DB_PASSWORD",
    "value": "my-secret-password",
    "description": "Database password for production"
  }'
```

### List Variables

```bash
curl "http://localhost:8000/api/agent/variables"
```

This will return a list of all variables (without their values).

### Get Variable Details

```bash
curl "http://localhost:8000/api/agent/variables/DB_PASSWORD"
```

This returns variable details without the actual value.

### Update a Variable

```bash
curl -X PUT "http://localhost:8000/api/agent/variables/DB_PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "value": "new-secret-password",
    "description": "Updated database password"
  }'
```

### Delete a Variable

```bash
curl -X DELETE "http://localhost:8000/api/agent/variables/DB_PASSWORD"
```

## Using Variables in Job Configurations

In your YAML job definition, reference variables using the `${VARIABLE_NAME}` syntax:

```yaml
sourceConfig:
  type: jdbc
  driver: com.mysql.cj.jdbc.Driver
  url: jdbc:mysql://localhost:3306/mydb
  username: ${DB_USERNAME}
  password: ${DB_PASSWORD}
```

When you submit this configuration through the API, all variable references will be replaced with their actual values before the job is submitted to Flink.

## Example

See the [flink_job_with_variables.yaml](./flink_job_with_variables.yaml) file for a complete example.

## Security Considerations

- Variable values are encrypted in the database using Fernet symmetric encryption
- The encryption key is derived from a secret key that should be set as an environment variable (`VARIABLE_ENCRYPTION_KEY`)
- In production, use a secure random value for the encryption key
- Access to the variables API should be restricted to authenticated users only

## System Variables

- `__NOW_TS10__`: current timestamp in seconds (10 digit timestamp)
- `__RANDOM_16BIT__`: random number between `0 <= value < 32767`
- `__SUUID_9__`: short UUID, 9 characters.
