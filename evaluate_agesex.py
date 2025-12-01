import os
import json
import requests

# ==========================================
# CONFIGURATION
# ==========================================

# Toggle to process all movies or just "a-different-man"
PROCESS_ALL_MOVIES = True 
TARGET_MOVIE_FOLDER = "a-different-man"

# Path to the root folder
ROOT_DIR = "dialogue_interactions"

# Ollama Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3"  # Knowledge cutoff < 2024

# Valid Categories
AGE_CLASSES = ["Toddler", "Child", "Adolescent", "Young Adult", "Adult", "Senior"]
SEX_CLASSES = ["Male", "Female"]

# Context Safety (Characters)
# Llama2 has a 4k token limit. ~12-14k chars is a safe upper bound.
MAX_CONTEXT_CHARS = 12000 

# ==========================================
# OLLAMA INTERACTION
# ==========================================

def query_ollama(prompt, model=MODEL_NAME):
    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json", 
        "stream": False,
        "options": {
            "temperature": 0.1, 
            "num_ctx": 4096
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

def get_char_mapping_and_text(interactions_list):
    """
    1. Identifies the two main characters.
    2. Maps them to 'Person A' and 'Person B'.
    3. Flattens ALL interactions into one long anonymized script.
    """
    unique_chars = []
    
    # 1. Identify Characters
    for interaction in interactions_list:
        for line in interaction:
            char_name = line.get("character", "Unknown")
            if char_name not in unique_chars:
                unique_chars.append(char_name)
    
    # 2. Create Mapping
    char_map = {} # Real Name -> Anon Name
    reverse_map = {} # Anon Name -> Real Name
    
    if len(unique_chars) > 0: 
        char_map[unique_chars[0]] = "Person A"
        reverse_map["Person A"] = unique_chars[0]
    if len(unique_chars) > 1: 
        char_map[unique_chars[1]] = "Person B"
        reverse_map["Person B"] = unique_chars[1]
    
    # Handle extras just in case
    for i, char in enumerate(unique_chars[2:]):
        anon = f"Person {chr(67+i)}"
        char_map[char] = anon
        reverse_map[anon] = char

    # 3. Flatten and Anonymize Text
    full_transcript = []
    
    for interaction in interactions_list:
        for line_obj in interaction:
            real_char = line_obj.get("character", "Unknown")
            anon_char = char_map.get(real_char, "Unknown")
            dialogue = line_obj.get("dialogue", "")
            full_transcript.append(f"{anon_char}: {dialogue}")
        full_transcript.append("--- [New Interaction] ---")

    combined_text = "\n".join(full_transcript)

    # 4. Truncate if too long to fit in context window
    # Strategy: Keep the beginning (intros) and end (resolutions), cut the middle.
    if len(combined_text) > MAX_CONTEXT_CHARS:
        half_limit = int(MAX_CONTEXT_CHARS / 2)
        combined_text = combined_text[:half_limit] + "\n...[SECTION OMITTED FOR LENGTH]...\n" + combined_text[-half_limit:]

    return combined_text, reverse_map

def construct_prompt(anonymized_text):
    return f"""
You are an expert character profiler. Read the following dialogue transcript between Person A and Person B. 
Analyze their vocabulary, tone, life stage references, and physical descriptions to determine their Sex and Age Class.

POSSIBLE AGES: {", ".join(AGE_CLASSES)}
(Definitions: Toddler: 1-3, Child: 4-12, Adolescent: 13-19, Young Adult: 20-35, Adult: 36-65, Senior: 65+)

POSSIBLE SEXES: {", ".join(SEX_CLASSES)}

TRANSCRIPT:
{anonymized_text}

OUTPUT FORMAT:
Provide a JSON object exactly like this:
{{
  "Person A": {{ "age": "Adult", "sex": "Male" }},
  "Person B": {{ "age": "Adolescent", "sex": "Female" }}
}}
Do not add any other text.
"""

def clean_llm_json(response_text):
    """Parses LLM response, handling potential markdown wrapping."""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != -1:
                return json.loads(response_text[start:end])
        except:
            pass
    return None

def process_file(file_path, output_folder):
    filename = os.path.basename(file_path)
    print(f"Processing: {filename}...")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            interactions_list = json.load(f)
    except Exception as e:
        print(f"Failed to load {filename}: {e}")
        return

    if not interactions_list:
        print("  Empty file. Skipping.")
        return

    # 1. Prepare Data
    anonymized_text, reverse_map = get_char_mapping_and_text(interactions_list)
    
    # 2. Query LLM
    prompt = construct_prompt(anonymized_text)
    response = query_ollama(prompt)
    
    if not response:
        print("  No response from LLM.")
        return

    # 3. Parse Result
    result = clean_llm_json(response)
    
    if result:
        final_output = []
        
        # We need to map the keys "Person A" back to real names and structure as requested
        # Requested Structure: [{ "char1": Name, "age": X, "sex": Y}, { "char2": Name ...}]
        
        # Handle Person A
        if "Person A" in reverse_map:
            data_a = result.get("Person A", {"age": "Unknown", "sex": "Unknown"})
            final_output.append({
                "char1": reverse_map["Person A"],
                "age": data_a.get("age", "Unknown"),
                "sex": data_a.get("sex", "Unknown")
            })
            
        # Handle Person B
        if "Person B" in reverse_map:
            data_b = result.get("Person B", {"age": "Unknown", "sex": "Unknown"})
            # Note: Using "char2" key for the second entry as per requested structure pattern
            final_output.append({
                "char2": reverse_map["Person B"],
                "age": data_b.get("age", "Unknown"),
                "sex": data_b.get("sex", "Unknown")
            })

        # 4. Save
        output_filename = f"llm-agesex_{filename}"
        output_path = os.path.join(output_folder, output_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, indent=2)
        print(f"  Saved: {output_path}")
        
    else:
        print(f"  Failed to parse JSON response: {response}")

# ==========================================
# MAIN LOOP
# ==========================================

def main():
    if not os.path.exists(ROOT_DIR):
        print(f"Error: Root folder '{ROOT_DIR}' not found.")
        return

    movie_folders = [f for f in os.listdir(ROOT_DIR) if os.path.isdir(os.path.join(ROOT_DIR, f))]

    for movie in movie_folders:
        if not PROCESS_ALL_MOVIES and movie != TARGET_MOVIE_FOLDER:
            continue
            
        movie_path = os.path.join(ROOT_DIR, movie)
        eval_folder = os.path.join(movie_path, "agesex_eval")
        
        # Create output directory
        os.makedirs(eval_folder, exist_ok=True)

        for file in os.listdir(movie_path):
            # Only process conversation json files, ignore subfolders and relationship_eval
            if file.endswith(".json") and "relationship_eval" not in file and "agesex_eval" not in file:
                
                # Check naming convention: movie_char1_char2.json
                if file.startswith(movie):
                    full_path = os.path.join(movie_path, file)
                    process_file(full_path, eval_folder)

if __name__ == "__main__":
    main()