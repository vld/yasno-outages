# Yasno outages parser

## How to run
1. Create virtual env
```bash

```

## How to run the Python project

1. **Create a virtual environment**
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate 
   ```

2. **Install `uv`**
   ```bash
   pip install uv
   ```

3. **Install all required packages**
   ```bash
   uv sync
   ```

4. **Run the project**
   ```bash
   uv run main.py
   ```

## MariaDB
```sql
CREATE DATABASE IF NOT EXISTS outages;
CREATE TABLE IF NOT EXISTS outages.plans (date DATE NOT NULL, slots JSON, updated_on DATETIME, PRIMARY KEY (date));

CREATE USER IF NOT EXISTS 'yasno'@'%' IDENTIFIED BY 'yasno_password';
GRANT ALL PRIVILEGES ON outages.plans TO 'yasno'@'%';

SHOW DATABASES;

```

