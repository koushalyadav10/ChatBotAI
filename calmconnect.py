import streamlit as st
import base64
import os
import google.generativeai as genai
from typing import Dict, List

# Constants
BACKGROUND_IMAGE = "yadav.jpg"
DEFAULT_PROMPTS = {
    "affirmation": "Give a short positive affirmation for someone feeling anxious or overwhelmed.",
    "meditation": "Provide a 5-minute guided meditation to reduce stress and promote calmness."
}

def configure_gemini() -> genai.GenerativeModel:
    """Configure Gemini API and initialize the model."""
    try:
        genai.configure(api_key="AIzaSyBkHfugdNnpudlAFpV36TBOoD5EdUlR5ao")  # Replace with your actual API key
        return genai.GenerativeModel('gemini-2.0-flash')# Updated model name
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {str(e)}")
        st.stop()

def setup_background() -> None:
    """Set up background image if available."""
    if os.path.exists(BACKGROUND_IMAGE):
        with open(BACKGROUND_IMAGE, "rb") as f:
            bin_str = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{bin_str}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

def initialize_session() -> None:
    """Initialize session state variables."""
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'last_response' not in st.session_state:
        st.session_state.last_response = ""

def generate_response(model: genai.GenerativeModel, prompt: str) -> str:
    """Generate a response from the AI model."""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ Sorry, I encountered an error: {str(e)}"

def display_chat_history() -> None:
    """Display the conversation history."""
    for message in st.session_state.history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_user_message(model: genai.GenerativeModel) -> None:
    """Handle user input and generate response."""
    if user_input := st.chat_input("How can I support you today?"):
        # Add user message to history
        st.session_state.history.append({"role": "user", "content": user_input})
        
        # Generate and display response
        with st.spinner("Thinking..."):
            response = generate_response(model, user_input)
            st.session_state.history.append({"role": "assistant", "content": response})
            st.session_state.last_response = response
            st.rerun()

def create_tool_buttons(model: genai.GenerativeModel) -> None:
    """Create buttons for special tools."""
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🌟 Positive Affirmation"):
            response = generate_response(model, DEFAULT_PROMPTS["affirmation"])
            st.session_state.history.append({"role": "assistant", "content": response})
            st.rerun()
    
    with col2:
        if st.button("🧘 Guided Meditation"):
            response = generate_response(model, DEFAULT_PROMPTS["meditation"])
            st.session_state.history.append({"role": "assistant", "content": response})
            st.rerun()

def main() -> None:
    """Main application function."""
    # Setup the app
    st.set_page_config(page_title="🧘Queue Management Chatbot", page_icon="🧘")
    setup_background()
    initialize_session()
    
    # Initialize Gemini model
    model = configure_gemini()
    
    # UI Components
    st.title("🧘 Queue Management  Chatbot")
    st.caption("A safe space for Wating wellbeing and support")
    
    # Display chat and handle interaction
    display_chat_history()
    handle_user_message(model)
    create_tool_buttons(model)

if __name__ == "__main__":
    main()