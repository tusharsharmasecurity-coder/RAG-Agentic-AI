from sqlalchemy import URL, create_engine
from src.config import settings

def get_engine():
    if settings.database_url:
        database_url = settings.database_url
    else:
        db_user, db_password = settings.require_database_credentials()
        database_url = URL.create(
            "mysql+pymysql",
            username=db_user,
            password=db_password,
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
        )
    return create_engine(database_url, echo=False, pool_pre_ping=True)


# Kept for legacy imports. New code should request an engine at the point of use.
engine = None
