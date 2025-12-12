# Movie Dialogue & Relationship Dataset (2024-2025)

v1.0 - 12.12.2025

## Overview

This dataset contains a corpus of official movie scripts released between 1.1.2024, and 1.3.2025. It focuses on screenplays nominated or submitted for scriptwriting awards and excludes biographies or stories inlcuding real people. 

In addition to raw scripts, the dataset provides processed data focusing on character interactions, specifically isolated dialogue between character pairs and provides a groundtruth of character attributes (sex, age, age-class, location, occupation and relationship status) as well as annotated relationship classifications between character pairs (Romantic, Platonic, Antagonistic, Professional, Familial) with textual evidence.

## Dataset Criteria

*   **Release Window:** Jan 1, 2024 – Mar 1, 2025.
*   **Source:** Official scripts (Award season nominations/submissions).
*   **Exclusions:** Biopics and stories based on real people were removed

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
*   **`chars_dict`**: Json file containing characters and their frequency of appearance.
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

## Source & Attribution

*   **Scripts Source:** Imsdb.com, indiewire.com, scriptslug.com
*   **Processing Method:** Mostly manual

