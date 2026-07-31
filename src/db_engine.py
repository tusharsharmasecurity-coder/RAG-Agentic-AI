from sqlalchemy import create_engine

DATABASE_URL = (
    "mysql+pymysql://root:YOUME%409299@localhost:3306/delhivery_ai"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)