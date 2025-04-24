import streamlit as st
import base64
import os
import google.generativeai as genai
from typing import Dict, List

# Constants
BACKGROUND_IMAGE = "queue_bg.jpg"  # You can change this to a queue management themed image
QUEUE_DATA = {
    "tables": {
        1: {"status": "occupied", "customer": "John Doe", "wait_time": "5 min"},
        2: {"status": "occupied", "customer": "Jane Smith", "wait_time": "10 min"},
        3: {"status": "available", "customer": "", "wait_time": ""},
        4: {"status": "occupied", "customer": "Mike Johnson", "wait_time": "15 min"},
    },
    "counters": {
        1: {"current": "A101", "status": "serving", "customer": "Sarah Williams"},
        2: {"current": "B205", "status": "serving", "customer": "Robert Brown"},
        3: {"current": "C301", "status": "waiting", "customer": "Emily Davis"},
    }
}

def configure_gemini() -> genai.GenerativeModel:
    """Configure Gemini API and initialize the model."""
    try:
        genai.configure(api_key="AIzaSyBkHfugdNnpudlAFpV36TBOoD5EdUlR5ao")  # Replace with your actual API key
        return genai.GenerativeModel('gemini-2.0-flash')
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

def generate_queue_response(model: genai.GenerativeModel, prompt: str) -> str:
    """Generate a response about queue status based on user query."""
    try:
        # Check if user is asking about their turn
        if "my turn" in prompt.lower() or "when" in prompt.lower() or "status" in prompt.lower():
            # Extract name and counter/table number from prompt (simple approach)
            name = None
            number = None
            
            # This is a simple extraction - you might want to use more sophisticated NLP
            words = prompt.split()
            for i, word in enumerate(words):
                if word.lower() in ["table", "counter"] and i+1 < len(words):
                    try:
                        number = int(words[i+1])
                    except ValueError:
                        pass
                elif word.lower() == "name" and i+1 < len(words):
                    name = " ".join(words[i+1:])
            
            # If we found a number, look up status
            if number is not None:
                if 1 <= number <= 3:  # Counter
                    counter = QUEUE_DATA["counters"].get(number, {})
                    if counter.get("customer", "").lower() == name.lower() if name else True:
                        status = f"Counter {number} is currently {counter.get('status', 'unknown')}"
                        if counter.get("status") == "serving":
                            return f"{status} with token {counter.get('current', '')} for {counter.get('customer', '')}. It's your turn now!"
                        else:
                            return f"{status}. Your token {counter.get('current', '')} is in queue. Estimated wait time: {10*number} minutes."
                    else:
                        return f"Counter {number} is currently {counter.get('status', 'unknown')} with token {counter.get('current', '')} for {counter.get('customer', '')}."
                elif 1 <= number <= 4:  # Table
                    table = QUEUE_DATA["tables"].get(number, {})
                    if table.get("customer", "").lower() == name.lower() if name else True:
                        status = f"Table {number} is currently {table.get('status', 'unknown')}"
                        if table.get("status") == "occupied":
                            return f"{status} by {table.get('customer', '')}. Your estimated wait time is {table.get('wait_time', 'unknown')}."
                        else:
                            return f"{status}. You can be seated now!"
                    else:
                        return f"Table {number} is currently {table.get('status', 'unknown')}."
            
            # If no specific number found, give general queue info
            general_info = "Current Queue Status:\n"
            general_info += "\nCounters:\n"
            for counter_num, counter_data in QUEUE_DATA["counters"].items():
                general_info += f"Counter {counter_num}: {counter_data['status']} - {counter_data['current']} ({counter_data['customer']})\n"
            
            general_info += "\nTables:\n"
            for table_num, table_data in QUEUE_DATA["tables"].items():
                general_info += f"Table {table_num}: {table_data['status']}"
                if table_data["status"] == "occupied":
                    general_info += f" - {table_data['customer']} ({table_data['wait_time']} wait)"
                general_info += "\n"
            
            return general_info
        
        # For other queue-related questions, use Gemini
        response = model.generate_content(
            f"You are a queue management assistant. Only answer questions about queue status, "
            f"waiting times, table availability, or counter service. For anything else, say "
            f"'I can only help with queue management questions.' The user asked: {prompt}"
        )
        return response.text
        
    except Exception as e:
        return f"⚠️ Sorry, I encountered an error processing your queue request: {str(e)}"

def display_chat_history() -> None:
    """Display the conversation history in a compact format."""
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.history[-5:]:  # Show only last 5 messages
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

def handle_user_message(model: genai.GenerativeModel) -> None:
    """Handle user input and generate response about queue status."""
    if user_input := st.chat_input("Ask about your queue status (e.g., 'When is my turn at counter 1?')"):
        # Add user message to history
        st.session_state.history.append({"role": "user", "content": user_input})
        
        # Generate and display response
        with st.spinner("Checking queue..."):
            response = generate_queue_response(model, user_input)
            st.session_state.history.append({"role": "assistant", "content": response})
            st.session_state.last_response = response
            st.rerun()

def main() -> None:
    """Main application function."""
    # Setup the app with compact layout
    st.set_page_config(
        page_title="Queue Management Chat", 
        page_icon="📊",
        layout="centered"
    )
    
    # Set a smaller width for the chat interface
    st.markdown(
        """
        <style>
            .block-container {
                max-width: 800px;
                padding-top: 1rem;
                padding-bottom: 1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    setup_background()
    initialize_session()
    
    # Initialize Gemini model
    model = configure_gemini()
    
    # Compact UI Components
    st.title("📊 Queue Status Chat")
    st.caption("Ask about your table or counter status")
    
    # Display compact chat history
    display_chat_history()
    
    # Handle user input
    handle_user_message(model)

if __name__ == "__main__":
    main()