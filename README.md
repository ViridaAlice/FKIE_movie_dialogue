Here is the structure of a standard GitHub `README.md` based on your dataset description. I have formatted it in Markdown, ready to copy and paste.

I have used **`[INSERT ...]`** placeholders for information that is standard in READMEs but was not provided in your description (e.g., license, installation, sources).

***

# Movie Dialogue & Relationship Dataset (2024-2025)

**[INSERT VERSION NUMBER, e.g., v1.0.0]** | **[INSERT DATE]**

## Overview

This dataset contains a corpus of official movie scripts released between **January 1, 2024, and March 1, 2025**. The corpus focuses on screenplays nominated or submitted for scriptwriting awards, excluding biographies or stories based on real people. 

In addition to raw scripts, the dataset provides processed data focusing on character interactions, specifically isolating dialogue between character pairs and providing annotated relationship classifications (e.g., Romantic, Platonic, Antagonistic) with textual evidence.

## Dataset Criteria

*   **Release Window:** Jan 1, 2024 – Mar 1, 2025.
*   **Source:** Official scripts (Award season nominations/submissions).
*   **Exclusions:** Biopics and stories based on real people were removed to focus on fictional character dynamics.

## Included Movies
The dataset currently includes the following titles:

*   A Different Man
*   All We Imagine as Light
*   Anora
*   A Real Pain
*   Babygirl
*   Blink Twice
*   Brutalist
*   Conclave
*   Daddio
*   Didi
*   Heretic
*   His Three Daughters
*   Hitman
*   I'm Still Here
*   I Saw the TV Glow
*   Juror #2
*   Memoir of a Snail
*   Nickel Boys
*   Nightbitch
*   Queer
*   The Last Showgirl
*   The Piano Lesson
*   The Room Next Door
*   The Seed of the Sacred Fig
*   The Substance
*   The Wild Robot
*   Thelma
*   Wicked

## Directory Structure

```text
root/
├── movies/
│   ├── a-different-man/
│   │   ├── chars           # List of characters (lowercase, newline separated)
│   │   ├── chars_dict      # Character frequency map
│   │   └── script          # Full raw text of the script
│   ├── anora/
│   └── ...
│
└── dialogue_interactions/
    ├── a-different-man/
    │   ├── relationships/  # Relationship annotations
    │   │   └── ..._relationships.json
    │   └── a-different-man_char1_char2.json
    ├── anora/
    └── ...
```

## Data Format Details

### 1. Movie Data (`/movies`)
Located in `movies/[movie-name]/`:

*   **`chars`**: A text file listing all characters found in the script, lowercase, separated by `\n`.
*   **`chars_dict`**: **[INSERT FILE TYPE, e.g., JSON or CSV]** containing characters and their frequency of appearance.
*   **`script`**: The full official script text.

### 2. Dialogue Interactions (`/dialogue_interactions`)
Located in `dialogue_interactions/[movie-name]/`. 
*   **Criteria:** Only character pairs with **> 10 interactions** are included.
*   **Naming Convention:** `[movie-name]_[char1]_[char2].json`

**JSON Structure:**
The file contains a list of interactions. Each item in the interaction list represents a single line of dialogue.

```json
[
  [
    {
      "character": "character name",
      "dialogue": "dialogue string",
      "movie": "movie-name"
    },
    {
      "character": "character name",
      "dialogue": "response string",
      "movie": "movie-name"
    }
  ],
  [ ... next interaction block ... ]
]
```

### 3. Relationship Annotations (`/relationships`)
Located in `dialogue_interactions/[movie-name]/relationships/`.
*   **Naming Convention:** `[char1]_[char2]_relationships.json` (or similar suffix).

**JSON Structure:**
Keyed by the Interaction ID (index) corresponding to the dialogue file.

```json
{
  "0": {
    "relationship": "Antagonistic", 
    "evidence": [
      {
        "line_indices": [0, 2],
        "text": "Copied text of interaction evidence...",
        "type": "Implied" 
      }
    ]
  },
  "1": {
    "relationship": "Professional",
    "evidence": [ ... ]
  }
}
```

*   **Relationship Categories:** `Platonic`, `Romantic`, `Antagonistic`, `Professional`, `Familial`.
*   **Evidence Type:** `Implied` or `Definitive`.

## Usage

**[INSERT INSTRUCTIONS ON HOW TO LOAD THE DATA, e.g.:]**

```python
import json
import os

# Example: Loading a dialogue interaction
with open('dialogue_interactions/anora/anora_ani_ivan.json', 'r') as f:
    data = json.load(f)
    print(data[0]) # Prints first interaction block
```

## Source & Attribution

*   **Scripts Source:** **[INSERT SOURCE OF SCRIPTS, e.g., Deadline "Read the Screenplay", Studio sites, etc.]**
*   **Processing Method:** **[INSERT BRIEF NOTES ON HOW CHARACTERS WERE EXTRACTED/PAIRS IDENTIFIED]**

## License

**[INSERT LICENSE HERE, e.g., MIT, CC-BY-NC, or "For Educational Use Only" due to copyright of scripts]**

## Citation

If you use this dataset in your research, please cite:

```text
[INSERT CITATION FORMAT HERE]
```
