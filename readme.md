# Yasno outages parser

## How to run

1. **Create a virtual environment**
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate 
   ```

1. **Install `uv`**
   ```bash
   pip install uv
   ```

1. **Install all required packages**
   ```bash
   uv sync
   ```

1. **Create env file**
   ```bash
   cp example.env .env
   ```
1. **Run the project**
   ```bash
   uv run --env-file .env main.py
   ```

## MariaDB scripts
```sql
CREATE DATABASE IF NOT EXISTS outages;
CREATE TABLE IF NOT EXISTS outages.plans (date DATE NOT NULL, slots JSON, updated_on DATETIME, PRIMARY KEY (date));

CREATE USER IF NOT EXISTS 'yasno'@'%' IDENTIFIED BY 'yasno_password';
GRANT ALL PRIVILEGES ON outages.plans TO 'yasno'@'%';

SHOW DATABASES;

```

https://app.yasno.ua/api/blackout-service/public/shutdowns/regions/25/dsos/902/planned-outages
