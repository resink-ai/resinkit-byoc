# Database Layer

This module provides the database layer for the ResinKit API using SQLAlchemy and Alembic with SQLite.

## Setup

The database uses SQLite as the backend and is configured in `resinkit_api/core/config.py`. By default, the database file is created at the project root as `sqlite.db`.

## Models

The database models are defined in `models.py` and include:

- `Task`: Represents a task with various attributes such as ID, type, status, creation time, etc.
- `TaskEvent`: Represents events associated with a task, such as status changes, with a foreign key relationship to the `Task` model.

## Database Operations

The CRUD operations for the models are defined in `crud.py` and include functions to:

- Create, read, update, and delete tasks
- Retrieve task events
- Filter tasks by various criteria

## FastAPI Integration

The API endpoints for interacting with the database are defined in `resinkit_api/api/endpoints/tasks.py` and are mounted to the FastAPI application in `main.py`.

## Database Migrations with Alembic

### What is Alembic?

Alembic is a lightweight database migration tool for SQLAlchemy that allows you to:

- Track changes to your database schema
- Generate migration scripts automatically based on changes to your SQLAlchemy models
- Apply migrations to update the database schema
- Rollback migrations if needed

### The script.py.mako File

The `script.py.mako` file is a template used by Alembic to generate migration scripts. It is located at `resinkit_api/db/alembic/script.py.mako`. Key points about this file:

1. **Purpose**: It provides a template for each new migration script, ensuring a consistent format.
2. **Content**: It includes imports, revision identifiers, and empty upgrade/downgrade functions.
3. **Customization for SQLite**: For this project, the file has been customized to:
   - Import the `JSONString` custom type and `TaskStatus` enum from our models
   - Import additional SQLAlchemy types needed for our schema
   - Include imports for working with SQLite

No specific modifications are required for SQLite, but the `render_as_batch=True` option has been added to the Alembic environment configuration to handle SQLite's limitations with ALTER TABLE statements.

### Database Migration Workflow

To work with database migrations:

1. **Initialize Alembic** (already done):

   ```
   cd resinkit_api/db
   alembic init alembic
   ```

2. **Generate a migration**:

   ```
   cd resinkit_api/db
   alembic revision --autogenerate -m "create_initial_tables"
   ```

   This will create a new migration script in the `alembic/versions` directory.

3. **Apply migrations**:

   ```
   cd resinkit_api/db
   alembic upgrade head
   ```

   This will apply all pending migrations to the database.

4. **Rollback migrations** (if needed):
   ```
   cd resinkit_api/db
   alembic downgrade -1  # Rollback one revision
   ```

### Best Practices

- Always review auto-generated migration scripts before applying them.
- Test migrations in a development environment before applying them to production.
- Include migration upgrades and downgrades for each schema change.
- Use descriptive names for migration scripts.

## SQLite-Specific Considerations

SQLite has some limitations compared to other database systems:

1. **Limited ALTER TABLE support**: SQLite cannot drop columns or alter column types. Alembic works around this by using `render_as_batch=True` to recreate tables.
2. **No built-in JSON type**: We use a custom `JSONString` type to store JSON data as text.
3. **Conditional indexes**: For partial indexes (e.g., `WHERE active = 1`), we use SQLAlchemy's `sqlite_where` parameter.

## Development vs. Production

For development, you can either:

- Use the commented-out line in `main.py` to create tables automatically: `Base.metadata.create_all(bind=engine)`
- Or use Alembic migrations which is the recommended approach for production

In production, always use Alembic migrations to manage schema changes.
