from sqlalchemy import create_engine
from src.schema_validator import SchemaValidator

engine = create_engine(
    "mysql+pymysql://root:YOUME%409299@localhost/delhivery_ai"
)

validator = SchemaValidator(engine)

print("Tables:")
print(validator.inspector.get_table_names())

print()

print("Shipment Columns:")
print(validator.get_columns("shipments"))