

# MariaDB
```sql
CREATE DATABASE IF NOT EXISTS outages;
CREATE TABLE IF NOT EXISTS outages.plans (date DATE NOT NULL, slots JSON, updated_on DATETIME, PRIMARY KEY (date));

CREATE USER IF NOT EXISTS 'yasno'@'%' IDENTIFIED BY 'yasno_password';
GRANT ALL PRIVILEGES ON outages.plans TO 'yasno'@'%';

SHOW DATABASES;

```

