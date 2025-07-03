from flask import Flask, render_template, request, jsonify
import os
import google.generativeai as genai
from pypdf import PdfReader, errors
from dotenv import load_dotenv
import re

load_dotenv()

app = Flask(__name__)

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

# Cache for party programs
party_programs = {}

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except errors.PdfStreamError as e:
        print(f"Error reading PDF file {file_path}: {e}")
        return None
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None

def load_party_programs():
    """Load all party programs from PDF files."""
    global party_programs
    party_programs_dir = "./partiprogram"
    
    if not os.path.exists(party_programs_dir):
        return
    
    for filename in os.listdir(party_programs_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(party_programs_dir, filename)
            text = extract_text_from_pdf(file_path)
            if text:
                party_name = filename.split(".")[0]
                party_programs[party_name] = text

def detect_party_from_message(message):
    """Detect which party the user is asking about."""
    message_lower = message.lower()
    
    # Common party name mappings
    party_mappings = {
        'arbeiderpartiet': 'arbeiderpartiets-partiprogram (1)',
        'ap': 'arbeiderpartiets-partiprogram (1)',
        'høyre': 'Høyres_stortingsvalgprogram_bokmal_ensidig',
        'høgre': 'Høyres_stortingsvalgprogram_bokmal_ensidig',
        'frp': 'FrP-Partiprogram-2025-2029',
        'fremskrittspartiet': 'FrP-Partiprogram-2025-2029',
        'krf': 'KRF_Partiprogram-2025-2029',
        'kristelig folkeparti': 'KRF_Partiprogram-2025-2029',
        'venstre': 'venstre-stortingsprogram-2025-2029'
    }
    
    for party_keyword, party_file in party_mappings.items():
        if party_keyword in message_lower:
            return party_file
    
    return None

def extract_relevant_content(party_text, question):
    """Extract relevant sections from party text based on question keywords."""
    question_lower = question.lower()
    
    # Define topic keywords and their related terms
    topic_keywords = {
        'skatt': ['skatt', 'avgift', 'skattetrykk', 'skattelette', 'skatteøkning', 'inntektsskatt', 'formuesskatt'],
        'innvandring': ['innvandring', 'flyktning', 'asyl', 'integrasjon', 'innvandrer', 'utlending'],
        'miljø': ['miljø', 'klima', 'forurensning', 'co2', 'karbon', 'bærekraft', 'grønn'],
        'helse': ['helse', 'sykehus', 'fastlege', 'helsetjeneste', 'medisin', 'behandling'],
        'utdanning': ['utdanning', 'skole', 'universitet', 'lærer', 'elev', 'student'],
        'arbeid': ['arbeid', 'jobb', 'arbeidsliv', 'arbeidstaker', 'arbeidsplasser', 'lønn'],
        'bolig': ['bolig', 'boligmarked', 'husleie', 'boliglån', 'boligpolitikk', 'boligbygging'],
        'familie': ['familie', 'barn', 'foreldre', 'foreldrepenger', 'barnehage', 'barnetrygd'],
        'transport': ['transport', 'kollektivtransport', 'vei', 'bane', 'fly', 'bil']
    }
    
    # Find relevant keywords in the question
    relevant_keywords = []
    for topic, keywords in topic_keywords.items():
        if any(keyword in question_lower for keyword in keywords):
            relevant_keywords.extend(keywords)
    
    # If no specific keywords found, use the first 12000 characters
    if not relevant_keywords:
        return party_text[:12000]
    
    # Split text into paragraphs
    paragraphs = party_text.split('\n')
    relevant_paragraphs = []
    
    # Find paragraphs containing relevant keywords
    for paragraph in paragraphs:
        paragraph_lower = paragraph.lower()
        if any(keyword in paragraph_lower for keyword in relevant_keywords):
            relevant_paragraphs.append(paragraph)
    
    # If we found relevant paragraphs, use them (up to 10000 chars)
    if relevant_paragraphs:
        relevant_text = '\n'.join(relevant_paragraphs)[:10000]
        return relevant_text
    
    # Fallback to first 12000 characters if no relevant sections found
    return party_text[:12000]

def answer_question_with_gemini(question, party_name, party_text):
    """Use Gemini to answer a question about a specific party."""
    if not api_key:
        return "Error: GEMINI_API_KEY not found in environment variables."
    
    # Extract relevant content based on the question
    relevant_content = extract_relevant_content(party_text, question)
    
    prompt = f"""Du er en politisk analytiker og ekspert på norsk politikk. Basert på partiprogrammet nedenfor, svar på følgende spørsmål så detaljert og nøyaktig som mulig.

Spørsmål: {question}

Partiprogram for {party_name}:
{relevant_content}

Instruksjoner:
- Gi et grundig og detaljert svar basert på partiprogrammet
- Trekk frem konkrete forslag og standpunkter fra programmet
- Hvis programmet inneholder relevant informasjon, forklar den grundig
- Bruk konkrete eksempler og tall fra programmet når de er tilgjengelige
- Hvis noe ikke står eksplisitt i programmet, nevn det, men forsøk å utlede basert på relaterte punkter
- Svar på norsk med en profesjonell og informativ tone
- Strukturer svaret med bullet points (*) for å gjøre det mer lesbart
- Bruk **fet skrift** for å fremheve viktige punkter og begreper
- Organiser informasjonen logisk med klare punkter"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Detect party from message
        detected_party = detect_party_from_message(user_message)
        
        if not detected_party:
            return jsonify({
                'response': 'Jeg forstår ikke hvilket parti du spør om. Vennligst spesifiser parti (f.eks. "Hva mener Høyre om skatt?" eller "FrP sin politikk på innvandring").'
            })
        
        # Get party program
        if detected_party not in party_programs:
            return jsonify({
                'response': f'Beklager, jeg finner ikke partiprogrammet for {detected_party}.'
            })
        
        party_text = party_programs[detected_party]
        
        # Get answer from Gemini
        answer = answer_question_with_gemini(user_message, detected_party, party_text)
        
        return jsonify({
            'response': answer,
            'party': detected_party
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/parties')
def get_parties():
    """Get list of available parties."""
    party_names = list(party_programs.keys())
    return jsonify({'parties': party_names})

if __name__ == '__main__':
    load_party_programs()
    app.run(debug=True, port=5000)