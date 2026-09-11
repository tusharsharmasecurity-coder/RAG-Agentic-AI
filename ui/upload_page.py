import streamlit as st
import pandas as pd
import requests
from src.database import Database
from src.db_engine import get_engine
from src.excel_importer import ExcelImporter
from src.schema_validator import SchemaValidator
from src.upload.data_cleaner import DataCleaner


def upload_page():
    st.title("📤 Upload Center")

    # Create two tabs to separate structured data (MySQL) from unstructured data (FAISS RAG)
    tab1, tab2 = st.tabs(
        ["📊 Database Upload (Excel/CSV)", "📚 AI Knowledge Base (PDF)"]
    )

    # ==========================================
    # TAB 1: YOUR EXISTING EXCEL/CSV PIPELINE
    # ==========================================
    with tab1:
        uploaded_file = st.file_uploader("Upload Excel / CSV", type=["xlsx", "csv"])

        if uploaded_file is not None:
            st.success("✅ STEP 1 - File Uploaded")

            try:
                if uploaded_file.name.endswith(".xlsx"):
                    df = pd.read_excel(uploaded_file)
                else:
                    df = pd.read_csv(uploaded_file)

                cleaner = DataCleaner()
                df = cleaner.clean(df)

                st.subheader("🧹 Cleaned Columns")
                st.write(df.columns.tolist())

                print("AFTER CLEANER")
                print(df.columns.tolist())

                st.success("✅ STEP 2 - Excel Read Successfully")

            except Exception as e:
                st.error(f"❌ Error Reading File\n\n{e}")
                st.stop()

            st.subheader("Preview")
            st.dataframe(df.head())

            st.success("✅ STEP 3 - Preview Displayed")

            try:
                importer = ExcelImporter()
                st.success("✅ STEP 4 - ExcelImporter Created")
            except Exception as e:
                st.error(f"❌ ExcelImporter Error\n\n{e}")
                st.stop()

            try:
                validator = SchemaValidator(get_engine())
                st.success("✅ STEP 5 - SchemaValidator Created")
            except Exception as e:
                st.error(f"❌ SchemaValidator Error\n\n{e}")
                st.stop()

            table_name = st.text_input("Table Name", value="shipments")

            st.success("✅ STEP 6 - Table Name Ready")

            try:
                st.write("Before table_exists")
                exists = importer.table_exists(table_name)
                st.write("After table_exists")
                st.success(f"✅ STEP 7 - table_exists() = {exists}")
            except Exception as e:
                st.error(f"❌ table_exists() Error\n\n{e}")
                st.stop()

            if exists:
                st.success("Table already exists.")
                try:
                    valid, result = validator.validate(df, table_name)
                    db_columns = validator.get_columns(table_name)

                    similarity = validator.compare(df.columns, db_columns)

                    st.success("✅ STEP 8 - Schema Validation Finished")

                    if valid:
                        st.success("Schema Matches")
                    else:
                        st.error("Schema Mismatch")
                        st.write(result)

                except Exception as e:
                    st.error(f"❌ Validation Error\n\n{e}")
                    st.stop()

                action = st.radio("Choose Action", ["Replace", "Append", "Cancel"])
            else:
                action = "Replace"

            if st.button("Import Into MySQL"):
                if action == "Cancel":
                    st.warning("Import Cancelled")
                else:
                    mode = "replace" if action == "Replace" else "append"

                    try:
                        rows = importer.import_excel(df, table_name, mode)
                        db = Database()

                        db.execute(f"""
                            UPDATE system_settings
                            SET setting_value='{table_name}'
                            WHERE setting_key='active_table'
                            """)

                        db.connection.commit()
                        db.close()

                        st.write("✅ Import Finished")
                        print("IMPORT FINISHED")
                        st.success("Imported Successfully")
                        st.success(f"✅ Imported {rows} rows successfully.")
                        st.cache_data.clear()

                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Import Error\n\n{e}")

    # ==========================================
    # TAB 2: DYNAMIC RAG (PDF UPLOAD)
    # ==========================================
    with tab2:
        st.markdown(
            "Upload new SOPs, policy updates, or training manuals to instantly train the AI."
        )

        pdf_file = st.file_uploader(
            "Drag and drop a PDF document here", type=["pdf"], key="pdf_uploader"
        )

        if st.button("Train AI with Document", type="primary"):
            if pdf_file is not None:
                with st.spinner(
                    f"Chunking and vectorizing '{pdf_file.name}' into FAISS..."
                ):
                    try:
                        files = {
                            "file": (
                                pdf_file.name,
                                pdf_file.getvalue(),
                                "application/pdf",
                            )
                        }
                        response = requests.post(
                            "http://127.0.0.1:8000/upload", files=files
                        )

                        if response.status_code == 200:
                            st.success(
                                f"✅ Successfully added '{pdf_file.name}' to the AI's knowledge base!"
                            )
                        else:
                            st.error(f"❌ Backend Error: {response.text}")
                    except Exception as e:
                        st.error(
                            f"🚨 Connection failed: Ensure your backend is running. Details: {e}"
                        )
            else:
                st.warning("⚠️ Please upload a PDF file first.")
