import mysql.connector
from src.config import settings
from langchain_core.documents import Document


def load_mysql_documents():

    user, password = settings.require_database_credentials()
    conn = mysql.connector.connect(
        host=settings.db_host, port=settings.db_port, user=user, password=password,
        database=settings.db_name,
    )
    

    cursor = conn.cursor()

    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()

    documents = []

    for table in tables:

        table_name = table[0]

        cursor.execute(f"SELECT * FROM {table_name}")

        columns = [desc[0] for desc in cursor.description]

        rows = cursor.fetchall()

        for row in rows:

            text = "\n".join(
                f"{col}: {value}"
                for col, value in zip(columns, row)
            )

            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": "mysql",
                        "table": table_name
                    }
                )
            )

    cursor.close()
    conn.close()

    print(f"[INFO] Loaded {len(documents)} MySQL records")

    return documents
