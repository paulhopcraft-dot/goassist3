# Database Migrations for Go Projects

Using [golang-migrate](https://github.com/golang-migrate/migrate) for database migrations.

## Setup

```bash
# Install migrate CLI
# macOS
brew install golang-migrate

# Linux
curl -L https://github.com/golang-migrate/migrate/releases/download/v4.16.2/migrate.linux-amd64.tar.gz | tar xvz
mv migrate /usr/local/bin/

# Windows
scoop install migrate
```

## Usage

### Create a New Migration

```bash
migrate create -ext sql -dir migrations -seq create_users_table
# Creates: migrations/000001_create_users_table.up.sql
#          migrations/000001_create_users_table.down.sql
```

### Run Migrations

```bash
# Up (apply migrations)
migrate -database "${DATABASE_URL}" -path migrations up

# Down (rollback migrations)
migrate -database "${DATABASE_URL}" -path migrations down

# Specific version
migrate -database "${DATABASE_URL}" -path migrations goto 2

# Force version (for fixing dirty state)
migrate -database "${DATABASE_URL}" -path migrations force 1
```

### Check Status

```bash
migrate -database "${DATABASE_URL}" -path migrations version
```

## Example Migration Files

### migrations/000001_create_users_table.up.sql

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### migrations/000001_create_users_table.down.sql

```sql
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP FUNCTION IF EXISTS update_updated_at_column();
DROP TABLE IF EXISTS users;
```

## In Code

### migrations.go

```go
package database

import (
    "database/sql"
    "fmt"
    "github.com/golang-migrate/migrate/v4"
    "github.com/golang-migrate/migrate/v4/database/postgres"
    _ "github.com/golang-migrate/migrate/v4/source/file"
)

func RunMigrations(db *sql.DB) error {
    driver, err := postgres.WithInstance(db, &postgres.Config{})
    if err != nil {
        return fmt.Errorf("could not create migration driver: %w", err)
    }

    m, err := migrate.NewWithDatabaseInstance(
        "file://migrations",
        "postgres",
        driver,
    )
    if err != nil {
        return fmt.Errorf("could not create migrate instance: %w", err)
    }

    if err := m.Up(); err != nil && err != migrate.ErrNoChange {
        return fmt.Errorf("could not run migrations: %w", err)
    }

    return nil
}
```

## Best Practices

1. **One Change Per Migration**: Keep migrations focused
2. **Always Write Down Migrations**: Every up needs a down
3. **Test Migrations**: Test both up and down
4. **Never Edit Applied Migrations**: Create new ones instead
5. **Use Transactions**: Wrap DDL in transactions where supported
6. **Version Control**: Commit migrations with code changes
