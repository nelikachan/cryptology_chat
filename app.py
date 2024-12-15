from flask import Flask, render_template, request, redirect, url_for, session
from ontology_parser import OntologyParser
from question_processor import QuestionProcessor
from answer_generator import AnswerGenerator
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # для работы с сессиями

# Initialize components
def init_components():
    ontology_parser = OntologyParser("crypto_2_1_1.rdf")
    question_processor = QuestionProcessor(ontology_parser)
    answer_generator = AnswerGenerator(ontology_parser)
    return ontology_parser, question_processor, answer_generator

# Load components
try:
    ontology_parser, question_processor, answer_generator = init_components()
except Exception as e:
    print(f"Error initializing components: {str(e)}")
    raise e

@app.route('/')
def home():
    if 'chat_history' not in session:
        session['chat_history'] = []
    return render_template('index.html', chat_history=session['chat_history'])

@app.route('/send_message', methods=['POST'])
def send_message():
    user_input = request.form.get('user_input')
    
    if user_input.strip():
        # Process user input
        try:
            processed_question = question_processor.process_question(user_input)
            answer = answer_generator.generate_answer(processed_question)
            
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
            
            # Update chat history
            if 'chat_history' not in session:
                session['chat_history'] = []
            
            session['chat_history'].append({'role': 'user', 'content': user_input})
            session['chat_history'].append({'role': 'assistant', 'content': answer})
            session.modified = True
            
        except Exception as e:
            pass  # Hide errors

    return redirect(url_for('home'))

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    session['chat_history'] = []
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)