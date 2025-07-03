import os
import google.generativeai as genai
from dotenv import load_dotenv
from utils import load_all_party_programs

load_dotenv()

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
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in .env file.")
        return

    genai.configure(api_key=api_key)

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
    party_programs_dir = "./partiprogram"
    party_programs = load_all_party_programs(party_programs_dir)

    user_answers = get_predefined_answers()
    analyze_with_gemini(user_answers, party_programs)
