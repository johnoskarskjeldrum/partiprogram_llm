#!/usr/bin/env python3
"""
Preprocessing script to convert party programs from PDF/Markdown to JSON cache.

The cache is included in the git repository for fast deployments.
Only run this script when adding or updating party programs, then commit the updated cache.

Usage: python preprocess_programs.py
"""

import os
import json
import hashlib
from datetime import datetime
from utils import extract_text_from_pdf, extract_text_from_markdown

def get_file_hash(file_path):
    """Generate MD5 hash of file for change detection."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def extract_topics_keywords(text):
    """Extract topic-based content sections for faster retrieval."""
    text_lower = text.lower()
    
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
    
    # Find paragraphs for each topic
    paragraphs = text.split('\n')
    topic_sections = {}
    
    for topic, keywords in topic_keywords.items():
        relevant_paragraphs = []
        for paragraph in paragraphs:
            paragraph_lower = paragraph.lower()
            if any(keyword in paragraph_lower for keyword in keywords):
                relevant_paragraphs.append(paragraph.strip())
        
        if relevant_paragraphs:
            topic_sections[topic] = '\n'.join(relevant_paragraphs)
    
    return topic_sections

def preprocess_party_program(file_path, cache_dir):
    """Process a single party program file and create JSON cache."""
    filename = os.path.basename(file_path)
    party_name = filename.split(".")[0]
    cache_file = os.path.join(cache_dir, f"{party_name}.json")
    
    # Check if cache exists and is up to date
    file_hash = get_file_hash(file_path)
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            if cached_data.get('file_hash') == file_hash:
                print(f"✓ Cache up to date: {filename}")
                return True
        except (json.JSONDecodeError, KeyError):
            pass  # Rebuild cache if corrupted
    
    print(f"Processing: {filename}...")
    
    # Extract text based on file type
    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif filename.endswith(".md"):
        text = extract_text_from_markdown(file_path)
    else:
        print(f"⚠ Skipping unsupported file: {filename}")
        return False
    
    if not text:
        print(f"✗ Failed to extract text from: {filename}")
        return False
    
    # Extract topic sections for fast retrieval
    topic_sections = extract_topics_keywords(text)
    
    # Create cache entry
    cache_entry = {
        "party_name": party_name,
        "display_name": get_display_name(party_name),
        "content": text,
        "topic_sections": topic_sections,
        "file_hash": file_hash,
        "source_file": filename,
        "processed_at": datetime.now().isoformat(),
        "content_length": len(text),
        "topics_found": list(topic_sections.keys())
    }
    
    # Write to cache
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_entry, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Cached: {filename} ({len(text):,} chars, {len(topic_sections)} topics)")
    return True

def get_display_name(party_name):
    """Convert filename-based party name to display name."""
    display_names = {
        "arbeiderpartiets": "Arbeiderpartiet",
        "hoyre": "Høyre", 
        "frp": "Fremskrittspartiet",
        "krf": "Kristelig Folkeparti",
        "venstre": "Venstre",
        "velferd_og_innovasjonspartiet": "Velferd og Innovasjonspartiet",
        "sosialistisk_vensterparti": "Sosialistisk Venstreparti",
        "rodt": "Rødt",
        "partiet_sentrum": "Partiet Sentrum",
        "pensjonistpartiet": "Pensjonistpartiet",
        "miljopartiet_de_gronne": "Miljøpartiet De Grønne",
        "konservativt": "Konservativt Folkeparti",
        "industri_og_næringspartiet": "Industri og Næringspartiet",
        "generasjonspartiet": "Generasjonspartiet",
        "fred_og_rettferdighet": "Fred og Rettferdighet",
        "norgesdemokratene": "Norgesdemokratene",
        "senterpartiet_partiprogram": "Senterpartiet",
        "partiet_dni": "Partiet DNI"
    }
    
    return display_names.get(party_name, party_name.replace('_', ' ').title())

def main():
    """Main preprocessing function."""
    programs_dir = "./partiprogram"
    cache_dir = "./cache"
    
    # Create cache directory
    os.makedirs(cache_dir, exist_ok=True)
    
    if not os.path.exists(programs_dir):
        print(f"✗ Programs directory not found: {programs_dir}")
        return False
    
    print("🔄 Preprocessing party programs...")
    print(f"Source: {programs_dir}")
    print(f"Cache: {cache_dir}")
    print("-" * 50)
    
    processed_count = 0
    failed_count = 0
    
    # Process all files in programs directory
    for filename in sorted(os.listdir(programs_dir)):
        if filename.endswith(('.pdf', '.md')):
            file_path = os.path.join(programs_dir, filename)
            if preprocess_party_program(file_path, cache_dir):
                processed_count += 1
            else:
                failed_count += 1
    
    print("-" * 50)
    print(f"✅ Preprocessing complete!")
    print(f"   Processed: {processed_count} files")
    if failed_count > 0:
        print(f"   Failed: {failed_count} files")
    
    # Create index file for fast directory listing
    cache_files = [f for f in os.listdir(cache_dir) if f.endswith('.json')]
    index = {
        "generated_at": datetime.now().isoformat(),
        "total_programs": len(cache_files),
        "programs": [f.replace('.json', '') for f in cache_files]
    }
    
    with open(os.path.join(cache_dir, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"📁 Created index with {len(cache_files)} programs")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)