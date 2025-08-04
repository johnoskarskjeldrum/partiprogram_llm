import os
import json
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

class PartyProgramCache:
    """Lazy-loading cache for party programs using preprocessed JSON files."""
    
    def __init__(self, cache_dir="./cache"):
        self.cache_dir = cache_dir
        self._programs = {}
        self._index = None
        self._load_index()
    
    def _load_index(self):
        """Load the cache index to know what programs are available."""
        index_path = os.path.join(self.cache_dir, 'index.json')
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f:
                    self._index = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load cache index: {e}")
                self._index = None
    
    def get_available_programs(self):
        """Get list of available program names without loading content."""
        if self._index:
            return self._index.get('programs', [])
        
        # Fallback: scan cache directory
        if not os.path.exists(self.cache_dir):
            return []
        
        programs = []
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json') and filename != 'index.json':
                programs.append(filename.replace('.json', ''))
        return programs
    
    def get_program(self, party_name):
        """Get a specific party program, loading from cache if needed."""
        # Return from memory cache if already loaded
        if party_name in self._programs:
            return self._programs[party_name]
        
        # Load from JSON cache
        cache_file = os.path.join(self.cache_dir, f"{party_name}.json")
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Cache the content in memory for future requests
            self._programs[party_name] = cache_data['content']
            return cache_data['content']
            
        except (json.JSONDecodeError, KeyError, IOError) as e:
            print(f"Error loading cached program {party_name}: {e}")
            return None
    
    def get_program_with_metadata(self, party_name):
        """Get program with full metadata (for advanced features)."""
        cache_file = os.path.join(self.cache_dir, f"{party_name}.json")
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading cached program metadata {party_name}: {e}")
            return None
    
    def get_all_programs(self):
        """Get all programs as a dictionary (for compatibility with existing code)."""
        programs = {}
        for party_name in self.get_available_programs():
            content = self.get_program(party_name)
            if content:
                programs[party_name] = content
        return programs
    
    def get_topic_content(self, party_name, topic):
        """Get content for a specific topic from a party program (optimized retrieval)."""
        cache_data = self.get_program_with_metadata(party_name)
        if not cache_data:
            return None
        
        # Return topic-specific content if available
        topic_sections = cache_data.get('topic_sections', {})
        if topic in topic_sections:
            return topic_sections[topic]
        
        # Fallback to full content
        return cache_data.get('content')
    
    def is_cache_available(self):
        """Check if the cache directory exists and has content."""
        return (os.path.exists(self.cache_dir) and 
                len(self.get_available_programs()) > 0)

def load_all_party_programs_cached(cache_dir="./cache", fallback_dir="./partiprogram"):
    """Load party programs using cache if available, fallback to direct loading."""
    cache = PartyProgramCache(cache_dir)
    
    if cache.is_cache_available():
        print(f"Loading party programs from cache ({len(cache.get_available_programs())} programs)")
        return cache.get_all_programs()
    else:
        print(f"Cache not available, falling back to direct loading from {fallback_dir}")
        print("Tip: Run 'python preprocess_programs.py' to build cache for faster loading")
        return load_all_party_programs(fallback_dir)
