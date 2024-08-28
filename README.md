# Data API

A pythonic interface for interacting with any PostGIS or PostgreSQL data warehouses.

## Installation

Create an env and then install this package into your env.

```python
pip install -e .
```

## Usage

First, create a .env.dwh file and define the following environment variables.

```bash
POSTGRES_USER="dwh_db_user"
POSTGRES_PASSWORD="dwh_db_pass"
POSTGRES_DB="dwh_db"
```

Then you can import it and access the database.

```python
from pathlib import Path
from dwh_api.catalog import DataCatalog

catalog = DataCatalog(Path("path/to/.env.dwh"))

results_df = catalog.query("SELECT * FROM a_schema.a_table")
```

I've also included some database inspection functionality, demonstrated below.

```python
catalog.get_schema_names()
['information_schema',
 'data_raw',
 'clean',
 'public',
 'tiger',
 'tiger_data',
 'topology']
```

