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

def extract_text_from_markdown(file_path):
    """Extracts text from a Markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error reading Markdown file {file_path}: {e}")
        return None

def load_all_party_programs(directory):
    """Loads all party programs from PDF and Markdown files in a given directory."""
    party_programs = {}
    if not os.path.exists(directory):
        print(f"Warning: Directory not found at {directory}")
        return party_programs
    
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(file_path)
        elif filename.endswith(".md"):
            text = extract_text_from_markdown(file_path)
        else:
            continue
            
        if text:
            party_name = filename.split(".")[0]
            party_programs[party_name] = text
            print(f"Loaded: {filename}")
    
    return party_programs
