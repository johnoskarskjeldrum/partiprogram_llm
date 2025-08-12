from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import google.generativeai as genai
from dotenv import load_dotenv
import re
from utils import load_all_party_programs, PartyProgramCache, load_all_party_programs_cached
from fuzzywuzzy import fuzz, process

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "a_very_secret_key_for_quiz_app")

# Configure Gemini API
api_key = os.getenv("GEMINI_API_KEY")
model = None
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

# Lazy-loading cache for party programs
party_cache = PartyProgramCache()
party_programs = {}  # Keep for compatibility, populated on-demand

def get_party_program(party_name):
    """Get a party program with lazy loading."""
    global party_programs
    if party_name not in party_programs:
        content = party_cache.get_program(party_name)
        if content:
            party_programs[party_name] = content
    return party_programs.get(party_name)

def get_all_party_programs():
    """Get all party programs, loading them lazily."""
    global party_programs
    available_programs = party_cache.get_available_programs()
    
    for party_name in available_programs:
        if party_name not in party_programs:
            content = party_cache.get_program(party_name)
            if content:
                party_programs[party_name] = content
    
    return party_programs


def detect_parties_from_message(message):
    """Detect which parties the user is asking about, avoiding generic terms."""
    message_lower = message.lower()
    print(f"DEBUG: Processing message for multiple parties: '{message}' -> '{message_lower}'")

    # Check for generic plural terms that imply a question about all parties.
    # Using word boundaries to avoid matching these within other words.
    if re.search(r'\bpartiene\b', message_lower) or re.search(r'\bpartia\b', message_lower):
        print("DEBUG: Generic party term found, returning no specific parties.")
        return []

    # Create comprehensive party name mappings from available programs
    party_name_mappings = {}
    available_programs = party_cache.get_available_programs()
    for filename_key in available_programs:
        # Extract common names from filenames based on actual files in partiprogram folder
        if "arbeiderpartiets" in filename_key:
            party_name_mappings['arbeiderpartiet'] = filename_key
            party_name_mappings['ap'] = filename_key
            party_name_mappings['arbeiderparti'] = filename_key
        elif "hoyre" in filename_key:
            party_name_mappings['hoyre'] = filename_key
            party_name_mappings['høyre'] = filename_key
            party_name_mappings['høgre'] = filename_key
            party_name_mappings['høre'] = filename_key
            party_name_mappings['høyr'] = filename_key
        elif "frp" in filename_key:
            party_name_mappings['frp'] = filename_key
            party_name_mappings['fremskrittspartiet'] = filename_key
            party_name_mappings['fremskritt'] = filename_key
        elif "krf" in filename_key:
            party_name_mappings['krf'] = filename_key
            party_name_mappings['kristelig folkeparti'] = filename_key
            party_name_mappings['kristelig'] = filename_key
        elif "venstre" in filename_key:
            party_name_mappings['venstre'] = filename_key
            party_name_mappings['venstrepartiet'] = filename_key
        elif "velferd_og_innovasjonspartiet" in filename_key:
            party_name_mappings['vipartiet'] = filename_key
            party_name_mappings['velferd og innovasjonspartiet'] = filename_key
            party_name_mappings['velferdspartiet'] = filename_key
        elif "sosialistisk_vensterparti" in filename_key:
            party_name_mappings['sv'] = filename_key
            party_name_mappings['sosialistisk venstreparti'] = filename_key
            party_name_mappings['sosialistisk'] = filename_key
        elif "rodt" in filename_key:
            party_name_mappings['rødt'] = filename_key
            party_name_mappings['rodt'] = filename_key
        elif "partiet_sentrum" in filename_key:
            party_name_mappings['partiet sentrum'] = filename_key
            party_name_mappings['sentrum'] = filename_key
            party_name_mappings['sentrumspartiet'] = filename_key
        elif "pensjonistpartiet" in filename_key:
            party_name_mappings['pensjonistpartiet'] = filename_key
            party_name_mappings['pensjonist'] = filename_key
        elif "miljopartiet_de_gronne" in filename_key:
            party_name_mappings['mdg'] = filename_key
            party_name_mappings['miljøpartiet de grønne'] = filename_key
            party_name_mappings['miljøpartiet'] = filename_key
            party_name_mappings['de grønne'] = filename_key
        elif "konservativt" in filename_key:
            party_name_mappings['konservativt'] = filename_key
            party_name_mappings['konservativ'] = filename_key
        elif "industri_og_næringspartiet" in filename_key:
            party_name_mappings['inp'] = filename_key
            party_name_mappings['industri og næringspartiet'] = filename_key
            party_name_mappings['industripartiet'] = filename_key
        elif "generasjonspartiet" in filename_key:
            party_name_mappings['generasjonspartiet'] = filename_key
            party_name_mappings['generasjon'] = filename_key
            party_name_mappings['generasjons'] = filename_key
        elif "fred_og_rettferdighet" in filename_key:
            party_name_mappings['fred og rettferdighet'] = filename_key
            party_name_mappings['fred'] = filename_key
        elif "norgesdemokratene" in filename_key:
            party_name_mappings['norgesdemokratene'] = filename_key
            party_name_mappings['norgesdemokrat'] = filename_key
        elif "senterpartiet_partiprogram" in filename_key:
            party_name_mappings['sp'] = filename_key
            party_name_mappings['senterpartiet'] = filename_key
            party_name_mappings['senter'] = filename_key
        elif "partiet_dni" in filename_key:
            party_name_mappings['dni'] = filename_key
            party_name_mappings['partiet dni'] = filename_key
            party_name_mappings['partiet d n i'] = filename_key
            party_name_mappings['d n i'] = filename_key

    detected_parties = set()
    
    # Sort by length (longest first) to prioritize longer, more specific matches
    sorted_mappings = sorted(party_name_mappings.items(), key=lambda x: len(x[0]), reverse=True)
    
    temp_message = message_lower
    for party_keyword, party_file in sorted_mappings:
        # Use word boundaries for more precise matching
        if re.search(r'\b' + re.escape(party_keyword) + r'\b', temp_message):
            detected_parties.add(party_file)
            # Replace the found keyword to avoid re-matching parts of it
            temp_message = temp_message.replace(party_keyword, "")

    print(f"DEBUG: Detected parties: {list(detected_parties)}")
    return list(detected_parties)


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

def generate_political_question(existing_questions, model_instance):
    """Generates a new, open-ended political question using Gemini, avoiding previously asked questions."""
    if not model_instance:
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
        response = model_instance.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating question: {e}")
        return "Kunne ikke generere et nytt spørsmål akkurat nå. Prøv igjen."

def summarize_user_stance(user_answers, model_instance):
    """Summarizes the user's political stance based on their answers using Gemini."""
    if not model_instance:
        return "Error: Gemini model not configured."

    answers_text = "\n".join([f"- Spørsmål: {q}\n  Svar: {a}" for q, a in user_answers.items()])

    prompt = f"""Du er en politisk analytiker. Basert på følgende spørsmål og svar fra en bruker, skriv en kort og nøytral oppsummering av brukerens politiske standpunkter. Fokuser på de viktigste temaene og tendensene i svarene. Oppsummeringen skal være på norsk.

Brukerens svar:
{answers_text}

Oppsummering av brukerens politiske standpunkt:
"""
    try:
        response = model_instance.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error summarizing user stance: {e}")
        return "Kunne ikke oppsummere dine standpunkter akkurat nå."

def match_user_to_party(user_stance_summary, party_programs, model_instance):
    """Compares the user's political stance to party programs and finds the best match using Gemini."""
    if not model_instance:
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
        response = model_instance.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error matching user to party: {e}")
        return "Kunne ikke finne en match akkurat nå."

def answer_question_with_gemini(question, party_data, model_instance):
    """Use Gemini to answer a question about one or more parties."""
    if not model_instance:
        return "Error: Gemini model not configured. GEMINI_API_KEY might be missing or invalid."

    if len(party_data) == 1:
        party_name = list(party_data.keys())[0]
        party_text = list(party_data.values())[0]
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

    else: # Multiple parties
        party_programs_text = ""
        for party_name, program_text in party_data.items():
            relevant_content = extract_relevant_content(program_text, question)
            party_programs_text += f"--- {party_name} ---\n{relevant_content}\n\n"

        prompt = f"""Du er en politisk analytiker og ekspert på norsk politikk. Du skal sammenligne flere partiers syn på et gitt spørsmål.

Spørsmål: {question}

Utdrag fra partiprogrammer:
{party_programs_text}

Instruksjoner:
- Sammenlign partienes standpunkter på spørsmålet.
- Trekk frem både likheter og forskjeller i partienes politikk.
- For hvert parti, presenter deres hovedsynspunkter og konkrete forslag.
- Strukturer svaret med en overskrift for hvert parti.
- Bruk bullet points (*) for å gjøre det enkelt å sammenligne.
- Bruk **fet skrift** for å fremheve viktige punkter.
- Avslutt med en kort oppsummering som trekker frem de viktigste forskjellene og likhetene.
- Svar på norsk med en profesjonell og nøytral tone."""

    try:
        response = model_instance.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    data = request.json
    gemini_api_key = data.get('gemini_api_key')
    if gemini_api_key:
        session['gemini_api_key'] = gemini_api_key
    else:
        session.pop('gemini_api_key', None) # Remove key if not provided

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

    # Get model for this request
    local_model = model
    gemini_api_key = session.get('gemini_api_key')
    if gemini_api_key:
        try:
            genai.configure(api_key=gemini_api_key)
            local_model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            return jsonify({'error': f"Invalid Gemini API Key: {e}"}), 400

    question = generate_political_question(asked_questions, local_model)
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

    # Get model for this request
    local_model = model
    gemini_api_key = session.get('gemini_api_key')
    if gemini_api_key:
        try:
            genai.configure(api_key=gemini_api_key)
            local_model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            return jsonify({'error': f"Invalid Gemini API Key: {e}"}), 400

    user_stance_summary = summarize_user_stance(user_answers, local_model)
    if "Error" in user_stance_summary or "Kunne ikke oppsummere" in user_stance_summary:
        return jsonify({'error': user_stance_summary}), 500

    match_result = match_user_to_party(user_stance_summary, get_all_party_programs(), local_model)
    if "Error" in match_result or "Kunne ikke finne en match" in match_result:
        return jsonify({'error': match_result}), 500

    session.pop('user_answers', None)
    session.pop('question_count', None)
    session.pop('asked_questions', None)
    session.pop('quiz_active', None)
    session.pop('gemini_api_key', None) # Clean up session

    return jsonify({'match_result': match_result})

@app.route('/chat', methods=['POST'])
def chat():
    global model
    try:
        data = request.json
        user_message = data.get('message', '')
        gemini_api_key = data.get('gemini_api_key')

        local_model = model
        if gemini_api_key:
            try:
                genai.configure(api_key=gemini_api_key)
                local_model = genai.GenerativeModel('gemini-1.5-flash')
            except Exception as e:
                return jsonify({'error': f"Invalid Gemini API Key: {e}"}), 400
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Detect parties from message
        detected_parties = detect_parties_from_message(user_message)
        
        party_data = {}
        if not detected_parties:
            # If no specific party is detected, assume the user is asking about all parties
            print("DEBUG: No specific party detected. Assuming a general question for all parties.")
            party_data = get_all_party_programs()
            detected_parties = list(party_data.keys()) # For the response JSON
        else:
            for party_file in detected_parties:
                content = get_party_program(party_file)
                if content:
                    party_data[party_file] = content
                else:
                    # This case should ideally not be hit if detection is accurate
                    return jsonify({
                        'response': f'Beklager, jeg finner ikke partiprogrammet for {party_file}.'
                    })

        if not party_data:
             # This is a fallback, in case detected_parties had content but none were found in party_programs
            return jsonify({'response': 'Jeg kunne ikke finne programmet for det valgte partiet. Prøv igjen.'})

        # Get answer from Gemini
        answer = answer_question_with_gemini(user_message, party_data, local_model)
        
        return jsonify({
            'response': answer,
            'parties': detected_parties
        })
        
    except Exception as e:
        print(f"Error in /chat endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/parties')
def get_parties():
    """Get list of available parties."""
    # Return a more user-friendly list of party names based on actual files
    user_friendly_party_names = []
    for filename_key in party_cache.get_available_programs():
        if "arbeiderpartiets" in filename_key:
            user_friendly_party_names.append('Arbeiderpartiet')
        elif "høyre" in filename_key:
            user_friendly_party_names.append('Høyre')
        elif "frp" in filename_key:
            user_friendly_party_names.append('FrP')
        elif "krf" in filename_key:
            user_friendly_party_names.append('KrF')
        elif "venstre" in filename_key:
            user_friendly_party_names.append('Venstre')
        elif "velferd_og_innovasjonspartiet" in filename_key:
            user_friendly_party_names.append('Velferd og Innovasjonspartiet')
        elif "sosialistisk_vensterparti" in filename_key:
            user_friendly_party_names.append('Sosialistisk Venstreparti')
        elif "rodt" in filename_key:
            user_friendly_party_names.append('Rødt')
        elif "partiet_sentrum" in filename_key:
            user_friendly_party_names.append('Partiet Sentrum')
        elif "pensjonistpartiet" in filename_key:
            user_friendly_party_names.append('Pensjonistpartiet')
        elif "miljopartiet_de_gronne" in filename_key:
            user_friendly_party_names.append('Miljøpartiet De Grønne')
        elif "konservativt" in filename_key:
            user_friendly_party_names.append('Konservativt')
        elif "industri_og_næringspartiet" in filename_key:
            user_friendly_party_names.append('Industri og Næringspartiet')
        elif "generasjonspartiet" in filename_key:
            user_friendly_party_names.append('Generasjonspartiet')
        elif "fred_og_rettferdighet" in filename_key:
            user_friendly_party_names.append('Fred og Rettferdighet')
        elif "norgesdemokratene" in filename_key:
            user_friendly_party_names.append('Norgesdemokratene')
        elif "senterpartiet_partiprogram" in filename_key:
            user_friendly_party_names.append('Senterpartiet')
        elif "partiet_dni" in filename_key:
            user_friendly_party_names.append('Partiet DNI')
    return jsonify({'parties': sorted(list(set(user_friendly_party_names)))})

@app.route('/debug/parties')
def debug_parties():
    """Debug endpoint to see what party programs are loaded."""
    return jsonify({
        'loaded_parties': party_cache.get_available_programs(),
        'party_count': len(party_cache.get_available_programs())
    })

@app.route('/debug/mappings')
def debug_mappings():
    """Debug endpoint to see party name mappings."""
    # Create the same mappings as in detect_party_from_message
    party_name_mappings = {}
    for filename_key in party_cache.get_available_programs():
        if "arbeiderpartiets" in filename_key:
            party_name_mappings['arbeiderpartiet'] = filename_key
            party_name_mappings['ap'] = filename_key
            party_name_mappings['arbeiderparti'] = filename_key
            party_name_mappings['arbeider'] = filename_key
        elif "hoyre" in filename_key:
            party_name_mappings['høyre'] = filename_key
            party_name_mappings['høgre'] = filename_key
            party_name_mappings['høre'] = filename_key
            party_name_mappings['hoyre'] = filename_key
        elif "frp" in filename_key:
            party_name_mappings['frp'] = filename_key
            party_name_mappings['fremskrittspartiet'] = filename_key
            party_name_mappings['fremskritt'] = filename_key
        elif "krf" in filename_key:
            party_name_mappings['krf'] = filename_key
            party_name_mappings['kristelig folkeparti'] = filename_key
            party_name_mappings['kristelig'] = filename_key
        elif "venstre" in filename_key:
            party_name_mappings['venstre'] = filename_key
            party_name_mappings['venstrepartiet'] = filename_key
        elif "velferd_og_innovasjonspartiet" in filename_key:
            party_name_mappings['vipartiet'] = filename_key
            party_name_mappings['velferd og innovasjonspartiet'] = filename_key
            party_name_mappings['velferdspartiet'] = filename_key
        elif "sosialistisk_vensterparti" in filename_key:
            party_name_mappings['sv'] = filename_key
            party_name_mappings['sosialistisk venstreparti'] = filename_key
            party_name_mappings['sosialistisk'] = filename_key
        elif "rodt" in filename_key:
            party_name_mappings['rødt'] = filename_key
            party_name_mappings['rodt'] = filename_key
        elif "partiet_sentrum" in filename_key:
            party_name_mappings['partiet sentrum'] = filename_key
            party_name_mappings['sentrum'] = filename_key
            party_name_mappings['sentrumspartiet'] = filename_key
        elif "pensjonistpartiet" in filename_key:
            party_name_mappings['pensjonistpartiet'] = filename_key
            party_name_mappings['pensjonist'] = filename_key
        elif "miljopartiet_de_gronne" in filename_key:
            party_name_mappings['mdg'] = filename_key
            party_name_mappings['miljøpartiet de grønne'] = filename_key
            party_name_mappings['miljøpartiet'] = filename_key
            party_name_mappings['de grønne'] = filename_key
        elif "konservativt" in filename_key:
            party_name_mappings['konservativt'] = filename_key
            party_name_mappings['konservativ'] = filename_key
        elif "industri_og_næringspartiet" in filename_key:
            party_name_mappings['inp'] = filename_key
            party_name_mappings['industri og næringspartiet'] = filename_key
            party_name_mappings['industripartiet'] = filename_key
        elif "generasjonspartiet" in filename_key:
            party_name_mappings['generasjonspartiet'] = filename_key
            party_name_mappings['generasjon'] = filename_key
            party_name_mappings['generasjons'] = filename_key
        elif "fred_og_rettferdighet" in filename_key:
            party_name_mappings['fred og rettferdighet'] = filename_key
            party_name_mappings['fred'] = filename_key
        elif "norgesdemokratene" in filename_key:
            party_name_mappings['norgesdemokratene'] = filename_key
            party_name_mappings['norgesdemokrat'] = filename_key
        elif "senterpartiet_partiprogram" in filename_key:
            party_name_mappings['sp'] = filename_key
            party_name_mappings['senterpartiet'] = filename_key
            party_name_mappings['senter'] = filename_key
        elif "partiet_dni" in filename_key:
            party_name_mappings['dni'] = filename_key
            party_name_mappings['partiet dni'] = filename_key
            party_name_mappings['partiet d n i'] = filename_key
            party_name_mappings['d n i'] = filename_key
    
    return jsonify({
        'party_mappings': party_name_mappings,
        'mapping_count': len(party_name_mappings)
    })

if __name__ == '__main__':
    # Check if cache is available, show helpful message if not
    if not party_cache.is_cache_available():
        print("⚠️  Party program cache not found!")
        print("   Run 'python preprocess_programs.py' to build cache for faster loading")
        print("   Starting with fallback loading (this will be slower)...")
    else:
        available_count = len(party_cache.get_available_programs())
        print(f"✅ Found cached party programs ({available_count} programs)")
    
    # Production-ready configuration
    import os
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') != 'production'
    
    print(f"🚀 Starting server on port {port} (debug={'on' if debug else 'off'})")
    app.run(debug=debug, port=port, host='0.0.0.0')