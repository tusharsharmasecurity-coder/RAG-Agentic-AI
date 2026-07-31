STANDARD_COLUMNS = [

    "shipment_id",

    "status",

    "origin_city",

    "destination_city",

    "customer_name",

    "warehouse",

    "delivery_date",

    "shipment_date",

    "priority",

    "weight",

    "damage_status",

    "delay_hours"

]
COLUMN_SYNONYMS = {

    "shipment_id":[
        "Shipment ID",
        "AWB",
        "AWB No",
        "Tracking Number",
        "Tracking ID",
        "Consignment Number",
        "Order Id"
    ],

    "status":[
        "Status",
        "Delivery Status",
        "Current Status",
        "Shipment Status"
    ],

    "origin_city":[
        "Origin",
        "Origin City",
        "Pickup City"
    ]
}