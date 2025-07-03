from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import google.generativeai as genai
from dotenv import load_dotenv
import re
from utils import load_all_party_programs

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "a_very_secret_key_for_quiz_app")

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
model = None
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

# Cache for party programs
party_programs = {}

def load_party_programs_into_cache():
    """Load all party programs into the global cache."""
    global party_programs
    party_programs_dir = "./partiprogram"
    party_programs = load_all_party_programs(party_programs_dir)


def detect_party_from_message(message):
    """Detect which party the user is asking about."""
    message_lower = message.lower()
    
    # Create dynamic party name mappings from loaded programs
    dynamic_party_mappings = {}
    for filename_key in party_programs.keys():
        # Extract common names from filenames (e.g., "arbeiderpartiets-partiprogram (1)" -> "arbeiderpartiet", "ap")
        if "arbeiderpartiets-partiprogram" in filename_key:
            dynamic_party_mappings['arbeiderpartiet'] = filename_key
            dynamic_party_mappings['ap'] = filename_key
        elif "Høyres_stortingsvalgprogram" in filename_key:
            dynamic_party_mappings['høyre'] = filename_key
            dynamic_party_mappings['høgre'] = filename_key
        elif "FrP-Partiprogram" in filename_key:
            dynamic_party_mappings['frp'] = filename_key
            dynamic_party_mappings['fremskrittspartiet'] = filename_key
        elif "KRF_Partiprogram" in filename_key:
            dynamic_party_mappings['krf'] = filename_key
            dynamic_party_mappings['kristelig folkeparti'] = filename_key
        elif "venstre-stortingsprogram" in filename_key:
            dynamic_party_mappings['venstre'] = filename_key
    
    for party_keyword, party_file in dynamic_party_mappings.items():
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
    
    # If no specific keywords found, use the first 20000 characters
    if not relevant_keywords:
        return party_text[:20000]
    
    # Split text into paragraphs
    paragraphs = party_text.split('\n')
    relevant_paragraphs = []
    
    # Find paragraphs containing relevant keywords
    for paragraph in paragraphs:
        paragraph_lower = paragraph.lower()
        if any(keyword in paragraph_lower for keyword in relevant_keywords):
            relevant_paragraphs.append(paragraph)
    
    # If we found relevant paragraphs, use them (up to 20000 chars)
    if relevant_paragraphs:
        relevant_text = '\n'.join(relevant_paragraphs)[:20000]
        return relevant_text
    
    # Fallback to first 20000 characters if no relevant sections found
    return party_text[:20000]

def generate_political_question(existing_questions):
    """Generates a new, open-ended political question using Gemini, avoiding previously asked questions."""
    global model
    if not model:
        return "Error: Gemini model not configured."

    prompt = f"""Du er en nøytral spørsmålsstiller for en politisk quiz. Generer ett nytt, åpent spørsmål om norsk politikk. Spørsmålet skal være generelt nok til at alle partier kan ha en mening om det, men spesifikt nok til å avdekke politiske standpunkter. Unngå spørsmål som kan besvares med et enkelt 'ja' eller 'nei'. Spørsmålet skal være på norsk.

Unngå disse tidligere stilte spørsmålene:
{', '.join(existing_questions)}

Eksempel på gode spørsmål:
- Hvordan bør Norge balansere økonomisk vekst med miljøhensyn?
- Hvilke tiltak er viktigst for å redusere sosiale ulikheter i Norge?
- Hvordan bør innvandringspolitikken tilpasses fremtidige behov i arbeidslivet?

Generer kun spørsmålet, ingen annen tekst.
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating question: {e}")
        return "Kunne ikke generere et nytt spørsmål akkurat nå. Prøv igjen."

def summarize_user_stance(user_answers):
    """Summarizes the user's political stance based on their answers using Gemini."""
    global model
    if not model:
        return "Error: Gemini model not configured."

    answers_text = "\n".join([f"- Spørsmål: {q}\n  Svar: {a}" for q, a in user_answers.items()])

    prompt = f"""Du er en politisk analytiker. Basert på følgende spørsmål og svar fra en bruker, skriv en kort og nøytral oppsummering av brukerens politiske standpunkter. Fokuser på de viktigste temaene og tendensene i svarene. Oppsummeringen skal være på norsk.

Brukerens svar:
{answers_text}

Oppsummering av brukerens politiske standpunkt:
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error summarizing user stance: {e}")
        return "Kunne ikke oppsummere dine standpunkter akkurat nå."

def match_user_to_party(user_stance_summary, party_programs):
    """Compares the user's political stance to party programs and finds the best match using Gemini."""
    global model
    if not model:
        return "Error: Gemini model not configured."

    party_programs_text = ""
    for party_name, program_text in party_programs.items():
        # Use a truncated version of the program for the prompt to save tokens
        party_programs_text += f"--- {party_name} ---\n{program_text[:5000]}\n\n" # Limit to first 5000 chars

    prompt = f"""Du er en ekspert på norsk politikk og en nøytral matchmaker. Du skal sammenligne en brukers politiske standpunkt med ulike norske partiers programmer.

Brukerens politiske standpunkt:
{user_stance_summary}

Partiprogrammer:
{party_programs_text}

Instruksjoner:
- Analyser brukerens standpunkt opp mot hvert partis program.
- Identifiser hvilket parti som best samsvarer med brukerens standpunkt.
- Gi en kort begrunnelse for hvorfor dette partiet er den beste matchen, og nevn kort hvorfor de andre partiene passer mindre godt.
- Svar på norsk.
- Start svaret med "Basert på dine svar, er partiet som best matcher dine politiske standpunkter: [Partinavn]."
- Deretter følger en begrunnelse.
"""
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error matching user to party: {e}")
        return "Kunne ikke finne en match akkurat nå."

def answer_question_with_gemini(question, party_name, party_text):
    """Use Gemini to answer a question about a specific party."""
    global model # Declare model as global to access the configured model
    if not model:
        return "Error: Gemini model not configured. GEMINI_API_KEY might be missing or invalid."
    
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

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    session['user_answers'] = {}
    session['question_count'] = 0
    session['asked_questions'] = []
    session['quiz_active'] = True
    return jsonify({'status': 'Quiz started', 'redirect_url': url_for('index')})

@app.route('/get_question', methods=['GET'])
def get_question():
    if not session.get('quiz_active'):
        return jsonify({'error': 'Quiz not active. Please start the quiz first.'}), 400

    question_count = session.get('question_count', 0)
    asked_questions = session.get('asked_questions', [])
    
    if question_count >= 5: # Ask 5 questions for the quiz
        return jsonify({'question': 'QUIZ_COMPLETE'})

    question = generate_political_question(asked_questions)
    if "Error" in question or "Kunne ikke generere" in question:
        return jsonify({'error': question}), 500
    
    asked_questions.append(question)
    session['asked_questions'] = asked_questions
    session['question_count'] = question_count + 1
    
    return jsonify({'question': question, 'question_number': session['question_count']})

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if not session.get('quiz_active'):
        return jsonify({'error': 'Quiz not active.'}), 400

    data = request.json
    question = data.get('question')
    answer = data.get('answer')

    if not question or not answer:
        return jsonify({'error': 'Missing question or answer'}), 400

    user_answers = session.get('user_answers', {})
    user_answers[question] = answer
    session['user_answers'] = user_answers
    
    return jsonify({'status': 'Answer submitted'})

@app.route('/get_match', methods=['GET'])
def get_match():
    if not session.get('quiz_active'):
        return jsonify({'error': 'Quiz not active.'}), 400
    
    user_answers = session.get('user_answers', {})
    if len(user_answers) < 5: # Ensure all questions are answered
        return jsonify({'error': 'Please answer all questions before getting a match.'}), 400

    user_stance_summary = summarize_user_stance(user_answers)
    if "Error" in user_stance_summary or "Kunne ikke oppsummere" in user_stance_summary:
        return jsonify({'error': user_stance_summary}), 500

    match_result = match_user_to_party(user_stance_summary, party_programs)
    if "Error" in match_result or "Kunne ikke finne en match" in match_result:
        return jsonify({'error': match_result}), 500

    session.pop('user_answers', None)
    session.pop('question_count', None)
    session.pop('asked_questions', None)
    session.pop('quiz_active', None)

    return jsonify({'match_result': match_result})

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
            # Provide a list of available parties if detection fails
            available_parties = ", ".join([p.replace('-', ' ').replace('_', ' ').replace('(1)', '').strip() for p in party_programs.keys()])
            return jsonify({
                'response': f'Jeg forstår ikke hvilket parti du spør om. Vennligst spesifiser parti (f.eks. "Hva mener Høyre om skatt?" eller "FrP sin politikk på innvandring"). Tilgjengelige partier er: {available_parties}.'
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
    # Return a more user-friendly list of party names
    user_friendly_party_names = []
    for filename_key in party_programs.keys():
        if "arbeiderpartiets-partiprogram" in filename_key:
            user_friendly_party_names.append('Arbeiderpartiet')
        elif "Høyres_stortingsvalgprogram" in filename_key:
            user_friendly_party_names.append('Høyre')
        elif "FrP-Partiprogram" in filename_key:
            user_friendly_party_names.append('FrP')
        elif "KRF_Partiprogram" in filename_key:
            user_friendly_party_names.append('KrF')
        elif "venstre-stortingsprogram" in filename_key:
            user_friendly_party_names.append('Venstre')
    return jsonify({'parties': sorted(list(set(user_friendly_party_names)))})

if __name__ == '__main__':
    load_party_programs_into_cache()
    app.run(debug=True, port=5000)