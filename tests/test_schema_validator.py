from src.schema_validator import SchemaValidator
from src.db_engine import engine

validator = SchemaValidator(engine)

print("Tables:")
print(validator.inspector.get_table_names())

print()

print("Shipment Columns:")
print(validator.get_columns("shipments"))
