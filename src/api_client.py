import requests
import streamlit as st

def ask_agent(question: str, thread_id: str = "default_thread"):
    try:
        payload = {
        "question": question,
        "thread_id": thread_id
        }
        # 👇 CHANGED TO DOCKER SERVICE NAME
        response = requests.post(
            "http://api:8000/ask",
            json=payload,
            timeout=120,
        )
        return response.json()

    except requests.exceptions.Timeout:
        st.error("🚨 API Timeout: The backend took longer than 120 seconds.")
        return {"answer": "Timeout error.", "intent": "UNKNOWN", "execution_time": 0.0}
        
    except requests.exceptions.ConnectionError:
        # 👇 Updated error message for accuracy
        st.error("🚨 Connection Error: Is the 'api' container running?")
        return {"answer": "Connection error.", "intent": "UNKNOWN", "execution_time": 0.0}
        
    except Exception as e:
        st.error(f"🚨 Unexpected UI Error: {str(e)}")
        return {"answer": "Unknown UI error.", "intent": "UNKNOWN", "execution_time": 0.0}