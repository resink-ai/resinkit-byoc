
# Database Layer System Design

## Backgroud

Following are the data tables we would like to store in sqlite3:

```sql
-- tasks Table
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    task_type TEXT NOT NULL,
    task_name TEXT,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'PENDING',
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    submitted_configs TEXT NOT NULL,  -- JSON as text
    error_info TEXT,                 -- JSON as text
    result_summary TEXT,             -- JSON as text
    execution_details TEXT,          -- JSON as text
    progress_details TEXT,           -- JSON as text
    created_by TEXT NOT NULL,
    notification_config TEXT,        -- JSON as text
    tags TEXT,                       -- JSON array as text
    active BOOLEAN NOT NULL DEFAULT 1,
    CHECK (status IN ('PENDING', 'SUBMITTED', 'VALIDATING', 'PREPARING', 'BUILDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLING', 'CANCELLED'))
);

-- Indexes for common query patterns
CREATE INDEX idx_tasks_status ON tasks(status) WHERE active = 1;
CREATE INDEX idx_tasks_task_type ON tasks(task_type) WHERE active = 1;
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_created_by ON tasks(created_by);

-- task_events Table
CREATE TABLE task_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data TEXT,                 -- JSON as text
    previous_status TEXT,
    new_status TEXT,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    actor TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id)
);

CREATE INDEX idx_task_events_task_id ON task_events(task_id);
CREATE INDEX idx_task_events_timestamp ON task_events(timestamp);
CREATE INDEX idx_task_events_event_type ON task_events(event_type);
```

## Designs

1.  **Project Setup and Dependencies:**
    * Tech stack: sqlite3 + alembic + sqlalchemy
    * Folders: sharable folders reside in db/ folder

2.  **SQLAlchemy Configuration:**
    * configure SQLAlchemy to connect to a SQLite database (e.g., `sqlite:///$DB_PATH/sql_app.db`), where $DB_PATH is a variable configured in config.py
    * Find a best place this configuration, perhaps using Pydantic for settings management.
    * Illustrate the creation of the SQLAlchemy engine and `SessionLocal`.
    * Define a `Base` class for declarative models.

3.  **SQLAlchemy Models:**
    * Translate the provided `tasks` and `task_events` SQL table definitions into SQLAlchemy Python models.
    * Ensure all columns, data types, primary keys, foreign keys, default values, and NOT NULL constraints are accurately represented.
    * Pay special attention to:
        * `TIMESTAMP` fields: How to define them with default values like `CURRENT_TIMESTAMP`.
        * `JSON as text` fields: Recommend how to handle these in SQLAlchemy. Should they be `String` types, or is there a better SQLAlchemy type for this when targeting SQLite (which doesn't have a native JSON type)? Discuss potential serialization/deserialization if needed.
        * `BOOLEAN` field with a default.
        * The `CHECK` constraint on `tasks.status`. How can this be represented or enforced at the SQLAlchemy model level or database level via Alembic?
        * The `FOREIGN KEY` relationship between `task_events.task_id` and `tasks.task_id`. Show how to define this relationship in the SQLAlchemy models (e.g., using `relationship` and `ForeignKey`).
    * Make sure tables are properly indexed

4.  **Alembic Setup for Database Migrations:**
    * Explain how to initialize Alembic in the project (`alembic init alembic`).
    * Guide on configuring Alembic's `env.py` file to:
        * Connect to the SQLite database using the SQLAlchemy engine.
        * Recognize the SQLAlchemy models defined in step 3 (i.e., set `target_metadata = Base.metadata`).
        * Include any necessary imports.
    * Explain the purpose of the `script.py.mako` file and if any modifications are needed for SQLite.
    * Mention how to configure `alembic.ini` for the database URL if not hardcoded in `env.py`.

5.  **Generating Initial Migration:**
    * Show the Alembic command to automatically generate the first migration script based on the defined SQLAlchemy models (`alembic revision -m "create_initial_tables" --autogenerate`).
    * Advise the user to review the generated migration script to ensure it accurately reflects the schema, including table creations, columns, constraints, and indexes. Specifically, how will the partial indexes (`WHERE active = 1`) and `CHECK` constraint be handled by autogenerate, and what manual adjustments might be needed in the migration script if Alembic doesn't perfectly capture them for SQLite?

6.  **Applying Migrations:**
    * Show the Alembic command to apply the migration to the database (`alembic upgrade head`).

7.  **FastAPI Integration (Basic Example):**
    * Briefly show how to create database tables on startup (if not solely relying on Alembic for creation, or for initial development).
    * Provide a simple example of a FastAPI path operation that interacts with one of the tables using `SessionLocal`.

8.  **Best Practices and Considerations:**
    * Managing JSON data: If using simple `String` types for JSON, mention the need for manual `json.dumps` and `json.loads`. Discuss if SQLAlchemy's `JSON` type can be used with a custom serializer/deserializer for SQLite.
    * `CURRENT_TIMESTAMP`: Ensure `server_default=func.now()` or similar is used for timestamp columns in SQLAlchemy.
    * Partial Indexes and CHECK constraints with Alembic and SQLite: Reiterate potential challenges and how to address them in migration scripts. SQLite has support for CHECK constraints directly in `CREATE TABLE`. For partial indexes, Alembic might need `op.create_index(..., sqlite_where=...)`.
    * Enum for status: Suggest using Python's `enum` type for the `status` field and how it can be mapped to SQLAlchemy.
