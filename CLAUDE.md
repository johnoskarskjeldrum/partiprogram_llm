# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Initial Setup
```bash
pip install -r requirements.txt
```
Create `.env` file with:
```
GEMINI_API_KEY="your_gemini_api_key_here"
FLASK_SECRET_KEY="optional_custom_secret_key"
```

### Preprocessing (Only when updating party programs)
```bash
python preprocess_programs.py
```
Converts PDF/Markdown party programs to JSON cache. The cache is included in git repository for fast deployments. Only run this when adding/updating party programs, then commit the updated cache.

### Running the Application
```bash
python app.py
```
Starts the Flask web server on port 8080. Will use cached programs if available, fallback to direct loading if not.

### Testing
```bash
python main.py
```
Runs analysis with predefined answers against party programs using Gemini API.

## Architecture

### Core Application Structure
- **app.py**: Main Flask application with two distinct modes - political quiz and Q&A chat
- **utils.py**: File processing utilities for loading PDF and Markdown party programs
- **main.py**: Testing script for analyzing predefined answers against party programs

### Party Program System
The application uses a two-tier loading system:
1. **Pre-built Cache**: JSON cache in `./cache/` directory is included in git repository (6MB) for instant deployments
2. **Lazy Loading**: `PartyProgramCache` class loads programs on-demand from JSON cache, with fallback to direct file loading

The cache includes topic extraction for faster content retrieval. When party programs are updated, run `preprocess_programs.py` locally and commit the updated cache.

### Dual-Mode Architecture
1. **Quiz Mode**: 5-question political stance assessment with session management
   - Generates dynamic questions using Gemini
   - Tracks user answers in Flask sessions
   - Analyzes political stance and matches to best-fitting party

2. **Chat Mode**: Direct Q&A about specific parties or general political topics
   - Detects party names from user messages using comprehensive mapping system
   - Extracts relevant content sections (max 20k chars) based on question keywords
   - Supports both single-party and multi-party comparisons

### Content Optimization
The system includes intelligent content extraction that:
- Maps political topics to relevant keywords (taxes, immigration, environment, etc.)
- Extracts only relevant paragraphs for efficient LLM processing
- Limits content to 20,000 characters per party to manage API costs

### Party Detection Logic
Complex fuzzy matching system in `detect_parties_from_message()` handles:
- Norwegian party name variations and abbreviations
- Word boundary matching to avoid false positives
- Longest-match-first algorithm for accurate detection
- Special handling for generic terms like "partiene" (the parties)

### Session Management
Quiz functionality uses Flask sessions to maintain state across:
- User answers collection
- Question generation tracking
- Quiz completion status
- Temporary session cleanup after analysis