import os

DEF_PSQL_URL = "postgresql+asyncpg://imgsmlr:imgsmlr-123456@127.0.0.1:5400/imgsmlr"

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8140"))
# https://docs.sqlalchemy.org/en/14/dialects/postgresql.html
POSTGRESQL_URL = os.environ.get("POSTGRESQL_URL", DEF_PSQL_URL)
SQL_DEBUG = False

SEARCH_LIMIT = int(os.environ.get("SEARCH_LIMIT", "20"))
SEARCH_SIMR_THRESHOLD = float(os.environ.get("SEARCH_SIMR_THRESHOLD", "1.5"))
