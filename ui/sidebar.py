import streamlit as st

def show_sidebar():
    with st.sidebar:
        # 1. Corporate Logo / Branding (Upgraded from plain text)
        st.markdown(
            """
            <div style='text-align: center; padding-bottom: 20px;'>
                <h2 style='color: #1E3A8A; font-weight: bold; margin-bottom: 0px;'>🚚 Delhivery AI</h2>
                <span style='color: #6B7280; font-size: 14px;'>Enterprise Logistics</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # 2. Active User Profile Card
        st.markdown(
            """
            <div style='background-color: #F3F4F6; padding: 15px; border-radius: 10px; border-left: 5px solid #10B981; margin-bottom: 20px;'>
                <h4 style='margin: 0px; color: #1F2937;'>👤 Tushar Sharma</h4>
                <p style='margin: 0px; color: #4B5563; font-size: 13px;'>Role: Admin / Operations</p>
                <p style='margin: 4px 0px 0px 0px; color: #10B981; font-size: 12px; font-weight: bold;'>● Active Session & Stateful</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        st.divider()
        
        # 3. Your Original Agent Architecture & Workflow Button (Preserved perfectly)
        st.markdown("### ⚙️ Agent Architecture")
        st.markdown("This system uses LangGraph to route intents dynamically between specialist agents.")
        
        if st.button("👀 View Agent Workflow", use_container_width=True):
            with st.spinner("Generating workflow diagram..."):
                try:
                    # DEFERRED IMPORT: Only load heavy agent libraries WHEN the button is clicked, 
                    # preventing Windows threading crashes during startup.
                    from ui.resources import get_agent
                    
                    agent = get_agent()
                    image_bytes = agent.orchestrator.get_workflow_image()
                    
                    if image_bytes:
                        st.image(image_bytes, caption="LangGraph State Machine")
                    else:
                        mermaid_code = agent.orchestrator.get_workflow_mermaid()
                        if mermaid_code:
                            st.markdown("```mermaid\n" + mermaid_code + "\n```")
                        else:
                            st.warning("Workflow graph rendering unavailable.")
                except Exception as exc:
                    st.error(f"Failed to load workflow: {exc}")