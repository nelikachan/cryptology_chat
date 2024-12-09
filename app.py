import streamlit as st
from ontology_parser import OntologyParser
from question_processor import QuestionProcessor
from answer_generator import AnswerGenerator
import os

# Set page configuration
st.set_page_config(page_title="Quantum Cryptography Assistant", page_icon="🤖", layout="wide")

# Custom CSS for chat-like interface
st.markdown("""
<style>
    .chat-container {
        max-width: 800px;
        margin: auto;
        padding: 20px;
    }
    
    .user-message {
        background-color: white;
        color: black;
        border-radius: 15px;
        padding: 10px 15px;
        margin: 5px 0;
        margin-left: 20%;
        margin-right: 5px;
        border: 1px solid #e9ecef;
    }
    
    .assistant-message {
        background-color: #007bff;
        color: white;
        border-radius: 15px;
        padding: 10px 15px;
        margin: 5px 0;
        margin-right: 20%;
        margin-left: 5px;
    }
    
    .message-container {
        display: flex;
        align-items: flex-start;
        margin-bottom: 10px;
    }
    
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin: 5px 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }
    
    .stTextInput>div>div>input {
        border-radius: 20px;
    }
    
    .main-title {
        text-align: center;
        color: #1e88e5;
        margin-bottom: 30px;
    }
    
    .stButton>button {
        border-radius: 20px;
        padding: 0.5rem 2rem;
    }
    
    div[data-testid="stToolbar"] {
        display: none;
    }
    
    .stDeployButton {
        display: none;
    }
    
    div[data-testid="stDecoration"] {
        display: none;
    }
    
    .stAlert {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Main interface
st.markdown("""
    <h1 class="main-title" style="font-family: 'Arial Black', sans-serif; font-weight: 900; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);">
        🔐 Quantum Cryptography Assistant
    </h1>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""

def handle_submit():
    user_input = st.session_state.user_input
    if user_input.strip():
        # Add user message to chat history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': user_input
        })
        
        # Process question and generate answer
        try:
            processed = question_processor.process_question(user_input)
            answer = answer_generator.generate_answer(processed)
            
            # Remove duplicate "Would you like to know anything else?" phrases
            answer_parts = answer.split("Would you like to know anything else? 😊")
            answer = "".join(answer_parts[:-1])  # Join all parts except the last one
            if answer_parts:  # Add the phrase only once at the end
                answer += "\nWould you like to know anything else? 😊"
            
            # Make links clickable in the answer
            answer = answer.replace("https://", '<a href="https://', -1).replace("</a>", "", -1)
            answer = answer.replace("http://", '<a href="http://', -1)
            for url in answer.split():
                if url.startswith(("http://", "https://")):
                    if '">' not in url:
                        answer = answer.replace(url, f'{url}">{url}</a>')
            
            # Add assistant's response to chat history
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': answer
            })
            
            # Clear input
            st.session_state.user_input = ""
            
        except Exception as e:
            pass  # Hide errors

# Initialize components
@st.cache_resource(show_spinner=False)
def init_components():
    try:
        ontology_parser = OntologyParser("crypto_2_1_1.rdf")
        question_processor = QuestionProcessor(ontology_parser)
        answer_generator = AnswerGenerator(ontology_parser)
        return ontology_parser, question_processor, answer_generator
    except Exception as e:
        st.error("Failed to initialize components. Please check if all requirements are installed.")
        return None, None, None

# Load components
try:
    ontology_parser, question_processor, answer_generator = init_components()
except Exception as e:
    st.error(f"Error initializing components: {str(e)}")
    st.stop()

# Display chat history
for message in st.session_state.chat_history:
    if message['role'] == 'user':
        st.markdown(f"""
        <div class="message-container" style="justify-content: flex-end">
            <div class="user-message">
                {message['content']}
            </div>
            <div class="avatar" style="background-color: #e9ecef;">👤</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="message-container">
            <div class="avatar" style="background-color: #007bff; color: white;">🤖</div>
            <div class="assistant-message">
                {message['content']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# Create columns for input and button
col1, col2 = st.columns([4, 1])

with col1:
    # User input
    st.text_input("Ask a question about quantum cryptography:", 
                  key="user_input", 
                  placeholder="Example: What is quantum key distribution?")

with col2:
    # Ask button
    st.button("Ask", on_click=handle_submit)

# Add some spacing at the bottom
st.markdown("<br><br>", unsafe_allow_html=True)

# Optional: Add a clear chat button
if st.button("Clear Chat"):
    st.session_state.chat_history = []
    st.rerun()