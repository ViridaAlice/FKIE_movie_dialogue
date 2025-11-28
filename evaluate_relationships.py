import os
import json
import requests
import re

# ==========================================
# CONFIGURATION
# ==========================================

# Toggle to process all movies or just "a-different-man"
PROCESS_ALL_MOVIES = False 
TARGET_MOVIE_FOLDER = "a-different-man"

# Path to the root folder
ROOT_DIR = "dialogue_interactions"

# Ollama Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
# Llama 2 was released in July 2023, fitting the < 1.1.2024 cutoff requirement.
# Ensure you have run `ollama pull llama2`
MODEL_NAME = "llama3" 

# Valid relationship categories
RELATIONSHIPS = ["Romantic", "Platonic", "Professional", "Antagonistic", "Familial"]

# ==========================================
# OLLAMA INTERACTION
# ==========================================

def query_ollama(prompt, model=MODEL_NAME):
    """Sends the prompt to Ollama and retrieves the JSON response."""
    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",  # Enforce JSON mode (supported in newer Ollama versions)
        "stream": False,
        "options": {
            "temperature": 0.1, # Low temperature for deterministic classification
            "num_ctx": 4096     # Ensure context window is large enough
        }
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Ollama: {e}")
        return None

# ==========================================
# DATA PROCESSING
# ==========================================

def anonymize_interaction(interaction_lines):
    """
    Replaces real character names with 'Person A' and 'Person B'.
    Returns the anonymized text lines (with indices) and the name mapping.
    """
    # Identify unique characters in order of appearance
    unique_chars = []
    for line in interaction_lines:
        char_name = line.get("character", "Unknown")
        if char_name not in unique_chars:
            unique_chars.append(char_name)
    
    # Create mapping (Only expecting 2 characters per file based on description)
    char_map = {}
    if len(unique_chars) > 0: char_map[unique_chars[0]] = "Person A"
    if len(unique_chars) > 1: char_map[unique_chars[1]] = "Person B"
    
    # Fallback for unexpected extra characters
    for i, char in enumerate(unique_chars[2:]):
        char_map[char] = f"Person {chr(67+i)}" # C, D, etc.

    anonymized_transcript = []
    
    for idx, line_obj in enumerate(interaction_lines):
        real_char = line_obj.get("character", "Unknown")
        anon_char = char_map.get(real_char, "Unknown")
        dialogue = line_obj.get("dialogue", "")
        
        # Store index and text for the prompt
        anonymized_transcript.append(f"[{idx}] {anon_char}: {dialogue}")

    return "\n".join(anonymized_transcript), char_map

def construct_prompt(anonymized_text):
    """Builds the prompt for the LLM."""
    return f"""
You are a relationship analyst. Analyze the following dialogue interaction between two characters (Person A and Person B).

TASK:
1. Classify the relationship between them into exactly one of these categories: {", ".join(RELATIONSHIPS)}.
2. Identify specific lines (by their [index]) that act as evidence for this classification.
3. Determine if the evidence is "Explicit" (directly stated) or "Implied" (subtext).

INPUT DIALOGUE:
{anonymized_text}

OUTPUT FORMAT:
Provide a raw JSON object. Do not explain. Follow this schema exactly:
{{
    "relationship": "Category",
    "evidence": [
      {{
        "line_indices": [0, 2],
        "text": "Full text of lines 0 and 2 combined...",
        "type": "Implied"
      }}
    ]
}}
"""

def clean_llm_json(response_text):
    """Attempts to clean and parse the LLM response into a Python dict."""
    try:
        # Try direct parse
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Heuristic: extract the first { and last }
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != -1:
                json_str = response_text[start:end]
                return json.loads(json_str)
        except:
            pass
    return None

def reconstruct_evidence_text(evidence_list, interaction_lines, char_map):
    """
    The LLM might hallucinate the text content or use the anonymized version.
    We rebuild the text field in the evidence using the real (or anonymized) text 
    based on the indices provided by the LLM to ensure accuracy.
    """
    # Reverse char map for display? Or keep Anonymized? 
    # The prompt implies the evidence text in the output example included "COOK: ..." 
    # so we should probably use the anonymized names to maintain the specific censorship requirement.
    
    for item in evidence_list:
        indices = item.get("line_indices", [])
        combined_text = []
        for idx in indices:
            if 0 <= idx < len(interaction_lines):
                line_obj = interaction_lines[idx]
                real_char = line_obj.get("character", "Unknown")
                anon_char = char_map.get(real_char, "Unknown")
                dialogue = line_obj.get("dialogue", "")
                combined_text.append(f"{anon_char}: {dialogue}")
        
        # Overwrite the text with the accurate reconstruction
        item["text"] = "\n".join(combined_text)
    return evidence_list

def process_file(file_path, movie_name, output_folder):
    filename = os.path.basename(file_path)
    print(f"Processing: {filename}...")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            interactions_list = json.load(f)
    except Exception as e:
        print(f"Failed to load {filename}: {e}")
        return

    output_data = {}

    for i, interaction in enumerate(interactions_list):
        # 1. Anonymize
        anonymized_text, char_map = anonymize_interaction(interaction)
        
        # 2. Prompt
        prompt = construct_prompt(anonymized_text)
        
        # 3. Call LLM
        response = query_ollama(prompt)
        if not response:
            print(f"  Skipping interaction {i} (No response)")
            continue

        # 4. Parse
        result = clean_llm_json(response)
        
        if result:
            # 5. Post-process evidence text (ensure it matches indices)
            if "evidence" in result:
                result["evidence"] = reconstruct_evidence_text(result["evidence"], interaction, char_map)
            
            output_data[str(i)] = result
        else:
            print(f"  Failed to parse JSON for interaction {i}")
            # Fallback empty structure
            output_data[str(i)] = {"relationship": "Unknown", "evidence": [], "error": "LLM Parse Failure"}

    # Write Output
    output_filename = f"llm-relationship_{filename}"
    output_path = os.path.join(output_folder, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    print(f"Saved: {output_path}")

# ==========================================
# MAIN LOOP
# ==========================================

def main():
    if not os.path.exists(ROOT_DIR):
        print(f"Error: Root folder '{ROOT_DIR}' not found.")
        return

    # List movie folders
    movie_folders = [f for f in os.listdir(ROOT_DIR) if os.path.isdir(os.path.join(ROOT_DIR, f))]

    for movie in movie_folders:
        # Filter logic
        if not PROCESS_ALL_MOVIES and movie != TARGET_MOVIE_FOLDER:
            continue
            
        movie_path = os.path.join(ROOT_DIR, movie)
        eval_folder = os.path.join(movie_path, "relationship_eval")
        
        # Create output directory
        os.makedirs(eval_folder, exist_ok=True)

        # Iterate JSON files
        for file in os.listdir(movie_path):
            if file.endswith(".json") and "relationship_eval" not in file:
                # Ensure we don't process files inside the 'relationships' subfolder if it exists
                # The loop os.listdir(movie_path) doesn't recurse, so folders are skipped, 
                # but we check extensions just in case.
                
                full_path = os.path.join(movie_path, file)
                
                # Double check naming convention to avoid processing non-dialogue files
                # Expecting: [movie]_[char1]_[char2].json
                if file.startswith(movie):
                    process_file(full_path, movie, eval_folder)

if __name__ == "__main__":
    main()