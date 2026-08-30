from faker import Faker
import random
import mysql.connector
from src.config import settings
from datetime import timedelta

fake = Faker("en_IN")

user, password = settings.require_database_credentials()
conn = mysql.connector.connect(
    host=settings.db_host, port=settings.db_port, user=user, password=password,
    database=settings.db_name,
)

cursor = conn.cursor()

warehouses = [
    "Delhi_Hub",
    "Mumbai_Bhiwandi",
    "Bangalore_Hoskote",
    "Hyderabad_Kompally",
    "Chennai_Oragadam",
    "Kolkata_Dankuni",
    "Pune_Chakan",
    "Ahmedabad_Sanand"
]

cities = [
    "Delhi",
    "Mumbai",
    "Bangalore",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Ahmedabad",
    "Kolkata"
]

statuses = [
    "Pending",
    "In Transit",
    "Delivered",
    "Returned",
    "Lost"
]

priorities = [
    "Low",
    "Medium",
    "High"
]

for i in range(10000):

    shipment_date = fake.date_between("-60d", "today")
    delivery_date = shipment_date + timedelta(days=random.randint(1, 10))

    sql = """
    INSERT INTO shipments(
        tracking_id,
        customer_name,
        origin_city,
        destination_city,
        warehouse,
        status,
        priority,
        weight,
        delay_hours,
        damage_status,
        shipment_date,
        delivery_date
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    values = (
        f"DL{random.randint(100000000,999999999)}",
        fake.name(),
        random.choice(cities),
        random.choice(cities),
        random.choice(warehouses),
        random.choice(statuses),
        random.choice(priorities),
        round(random.uniform(0.5, 40), 2),
        random.randint(0, 72),
        random.choice(["Yes", "No"]),
        shipment_date,
        delivery_date
    )

    cursor.execute(sql, values)

conn.commit()

print("✅ 10,000 shipments inserted.")

cursor.close()
conn.close()
