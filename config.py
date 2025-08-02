import os

DEF_PSQL_URL = "postgresql+asyncpg://imgsmlr:imgsmlr-123456@127.0.0.1:5400/imgsmlr"

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8140"))
# https://docs.sqlalchemy.org/en/14/dialects/postgresql.html
POSTGRESQL_URL = os.environ.get("POSTGRESQL_URL", DEF_PSQL_URL)
SQL_DEBUG = False

SEARCH_LIMIT = int(os.environ.get("SEARCH_LIMIT", "20"))
SEARCH_SIMR_THRESHOLD = float(os.environ.get("SEARCH_SIMR_THRESHOLD", "0.1"))

# 模型配置
SUPPORTED_MODELS = os.environ.get("SUPPORTED_MODELS", "all")  # clip, siglip, all
CLIP_MODEL = os.environ.get("CLIP_MODEL", "OFA-Sys/chinese-clip-vit-base-patch16")
SIGLIP_MODEL = os.environ.get("SIGLIP_MODEL", "google/siglip-base-patch16-224")

# 模型初始化配置
MODEL_INIT_TIMEOUT = int(os.environ.get("MODEL_INIT_TIMEOUT", "300"))  # 模型初始化超时时间（秒）
MODEL_DEBUG = os.environ.get("MODEL_DEBUG", "false").lower() == "true"  # 是否启用模型调试模式
