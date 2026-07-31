from sqlalchemy import create_engine

engine = create_engine(
    "mysql+pymysql://root:YOUME%409299@localhost:3306/delhivery_ai"
)

try:
    conn = engine.connect()
    print("Connected Successfully")
    conn.close()

except Exception as e:
    print(e)