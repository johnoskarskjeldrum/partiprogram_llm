import os
from pypdf import PdfReader, errors

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


def get_predefined_answers():
    """Returns a predefined set of answers for testing."""
    return {
        "Bør skattene økes for å finansiere velferdstjenester?": "ja",
        "Er du for eller mot strengere miljøavgifter?": "ja",
        "Bør Norge ta imot flere eller færre flyktninger?": "vet ikke",
        "Støtter du økt privatisering i helsevesenet?": "nei",
        "Bør vi ha en mer restriktiv eller liberal innvandringspolitikk?": "liberal",
    }


import os
import google.generativeai as genai
from pypdf import PdfReader, errors

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


def get_predefined_answers():
    """Returns a predefined set of answers for testing."""
    return {
        "Bør skattene økes for å finansiere velferdstjenester?": "ja",
        "Er du for eller mot strengere miljøavgifter?": "ja",
        "Bør Norge ta imot flere eller færre flyktninger?": "vet ikke",
        "Støtter du økt privatisering i helsevesenet?": "nei",
        "Bør vi ha en mer restriktiv eller liberal innvandringspolitikk?": "liberal",
    }


def analyze_with_gemini(user_answers, party_programs):
    """Analyzes user answers against party programs using the Gemini API."""
    # IMPORTANT: Replace with your actual API key
    genai.configure(api_key="YOUR_API_KEY")

    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = "Du er en politisk analytiker. Analyser brukerens svar og partiprogrammene. Ranger partiene fra den som passer best til den som passer dårligst. Gi en kort begrunnelse for rangeringen.\n\n"
    prompt += "Brukerens svar:\n"
    for question, answer in user_answers.items():
        prompt += f"- {question}: {answer}\n"

    prompt += "\nPartiprogrammer:\n"
    for party, program in party_programs.items():
        prompt += f"--- {party} ---\n"
        prompt += program[:2000]  # Use a sample of the program
        prompt += "\n\n"

    try:
        response = model.generate_content(prompt)
        print("\nResultat fra Gemini:")
        print(response.text)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    party_programs_dir = "/Users/johnoskarholmenskjeldrum/Projects/partiprogram_llm/partiprogram"
    party_programs = {}

    for filename in os.listdir(party_programs_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(party_programs_dir, filename)
            text = extract_text_from_pdf(file_path)
            if text:
                party_name = filename.split(".")[0]
                party_programs[party_name] = text

    user_answers = get_predefined_answers()
    analyze_with_gemini(user_answers, party_programs)
