from pathlib import Path
from typing import List,Any
from langchain_community.document_loaders import PyMuPDFLoader,TextLoader,CSVLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain_community.document_loaders.excel import UnstructuredExcelLoader
from langchain_community.document_loaders import JSONLoader
import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Any
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from src.mysql_loader import load_mysql_documents

def load_all_documents(data_dir: str) -> List[Any]:
    """
    Load all supported files from the data directory and convert to LangChain Document objects.

    Supported:
    - PDF
    - TXT
    - CSV
    - SQL (SQLite)
    """

    data_path = Path(data_dir).resolve()
    print(f"[DEBUG] Data path: {data_path}")

    documents = []

    # ==========================
    # PDF Files
    # ==========================
    pdf_files = list(data_path.glob("**/*.pdf"))
    print(f"[DEBUG] Found {len(pdf_files)} PDF files")

    for pdf_file in pdf_files:
        print(f"[DEBUG] Loading PDF: {pdf_file}")

        try:
            loader = PyPDFLoader(str(pdf_file))
            loaded = loader.load()

            print(f"[DEBUG] Loaded {len(loaded)} pages")

            documents.extend(loaded)

        except Exception as e:
            print(f"[ERROR] Failed to load {pdf_file}: {e}")

    # ==========================
    # TXT Files
    # ==========================
    txt_files = list(data_path.glob("**/*.txt"))
    print(f"[DEBUG] Found {len(txt_files)} TXT files")

    for txt_file in txt_files:
        print(f"[DEBUG] Loading TXT: {txt_file}")

        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                text = f.read()

            documents.append(
                Document(
                    page_content=text,
                    metadata={"source": str(txt_file)}
                )
            )

        except Exception as e:
            print(f"[ERROR] Failed to load {txt_file}: {e}")

    # ==========================
    # CSV Files
    # ==========================
    csv_files = list(data_path.glob("**/*.csv"))
    print(f"[DEBUG] Found {len(csv_files)} CSV files")

    for csv_file in csv_files:
        print(f"[DEBUG] Loading CSV: {csv_file}")

        try:
            df = pd.read_csv(csv_file)

            for i, row in df.iterrows():
                documents.append(
                    Document(
                        page_content=row.to_json(),
                        metadata={
                            "source": str(csv_file),
                            "row": i
                        }
                    )
                )

        except Exception as e:
            print(f"[ERROR] Failed to load {csv_file}: {e}")

    # ==========================
    # SQL Files (.sql)
    # ==========================

    sql_files = list(data_path.glob("**/*.sql"))
    print(f"[DEBUG] Found {len(sql_files)} SQL files")

    for sql_file in sql_files:
     print(f"[DEBUG] Loading SQL: {sql_file}")

    try:
        # Create an in-memory SQLite database
        conn = sqlite3.connect(":memory:")

        # Read the SQL script
        with open(sql_file, "r", encoding="utf-8") as f:
            sql_script = f.read()

        # Execute the SQL script
        conn.executescript(sql_script)

        cursor = conn.cursor()

        # Get all tables
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        )

        tables = cursor.fetchall()

        print(f"[DEBUG] Tables found: {tables}")

        # Read every table
        for table in tables:

            table_name = table[0]

            df = pd.read_sql_query(
                f"SELECT * FROM {table_name}",
                conn
            )

            print(f"[DEBUG] Loaded {len(df)} rows from {table_name}")

            for i, row in df.iterrows():

              documents.append(
                    Document(
                        page_content=row.to_json(),
                        metadata={
                            "source": str(sql_file),
                            "table": table_name,
                            "row": i,
                        },
                    )
                )

        conn.close()

    except Exception as e:
        print(f"[ERROR] Failed to load {sql_file}: {e}")

    print(f"[INFO] Total Documents Loaded: {len(documents)}")
    mysql_docs = load_mysql_documents()

    documents.extend(mysql_docs)
    return documents