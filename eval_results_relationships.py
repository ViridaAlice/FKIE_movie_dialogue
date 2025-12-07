import os
import json
import collections

# ==========================================
# CONFIGURATION
# ==========================================

ROOT_DIR = "dialogue_interactions"

# Mapping for Evidence Types (if you want to compare them strictly later)
# LLM uses "Explicit", GT uses "Definitive"
TYPE_MAP = {
    "Explicit": "Definitive",
    "Implied": "Implied"
}

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_line_indices(evidence_list):
    """
    Extracts a set of all unique line indices cited in an evidence list.
    """
    indices = set()
    if not evidence_list:
        return indices
    
    for item in evidence_list:
        lines = item.get("line_indices", [])
        for line in lines:
            indices.add(line)
    return indices

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None

# ==========================================
# MAIN EVALUATION LOGIC
# ==========================================

def main():
    # Statistics Containers
    # movie_stats[movie_name] = { 'correct_rel': 0, 'total_rel': 0, 'evidence_recall_sum': 0, 'evidence_count': 0 }
    movie_stats = collections.defaultdict(lambda: {
        'correct_rel': 0, 
        'total_rel': 0, 
        'evidence_recall_sum': 0.0, 
        'evidence_count': 0
    })

    # Global counters
    total_files_processed = 0

    # 1. Walk through the directory structure
    for root, dirs, files in os.walk(ROOT_DIR):
        
        # We only care about the LLM output folder
        if os.path.basename(root) == "relationship_eval":
            movie_name = os.path.basename(os.path.dirname(root))
            movie_dir = os.path.dirname(root)
            gt_folder = os.path.join(movie_dir, "relationships")

            # Check if GT folder exists
            if not os.path.exists(gt_folder):
                print(f"Skipping {movie_name}: No 'relationships' Ground Truth folder found.")
                continue

            for file in files:
                if file.startswith("llm-relationship_") and file.endswith(".json"):
                    llm_path = os.path.join(root, file)
                    
                    # 2. Construct Ground Truth Filename
                    # LLM: llm-relationship_[movie]_[char1]_[char2].json
                    # GT:  [movie]_[char1]_[char2]_relationships.json
                    
                    base_name = file.replace("llm-relationship_", "") # Remove prefix
                    gt_filename = base_name.replace(".json", "_relationships.json") # Add suffix
                    gt_path = os.path.join(gt_folder, gt_filename)

                    if not os.path.exists(gt_path):
                        # Try to handle potential minor naming mismatches if necessary
                        print(f"  Warning: GT file missing for {file}")
                        continue

                    # 3. Load Data
                    llm_data = load_json(llm_path)
                    gt_data = load_json(gt_path)

                    if not llm_data or not gt_data:
                        continue

                    total_files_processed += 1

                    # 4. Compare Interaction by Interaction
                    # We iterate through GT keys to ensure we are checking what SHOULD be there.
                    for interaction_id, gt_obj in gt_data.items():
                        
                        # Initialize metric for this specific interaction
                        is_rel_correct = False
                        evidence_recall = 0.0
                        
                        # Get corresponding LLM object
                        llm_obj = llm_data.get(interaction_id)

                        # --- A. Relationship Classification Accuracy ---
                        gt_rel = gt_obj.get("relationship", "").strip().lower()
                        
                        if llm_obj:
                            llm_rel = llm_obj.get("relationship", "").strip().lower()
                            if gt_rel == llm_rel:
                                is_rel_correct = True
                        
                        # Update Stats
                        movie_stats[movie_name]['total_rel'] += 1
                        if is_rel_correct:
                            movie_stats[movie_name]['correct_rel'] += 1

                        # --- B. Evidence Retrieval (Recall) ---
                        # "Additional evidence... shouldn't be counted as negative" -> Ignore Precision
                        # "Evidence that hasn't been found... should be negatively noted" -> Use Recall
                        
                        gt_indices = get_line_indices(gt_obj.get("evidence", []))
                        
                        if len(gt_indices) > 0:
                            if llm_obj:
                                llm_indices = get_line_indices(llm_obj.get("evidence", []))
                                
                                # Find intersection (Correctly identified lines)
                                common = gt_indices.intersection(llm_indices)
                                
                                # Recall = Matches / Total Expected
                                evidence_recall = len(common) / len(gt_indices)
                            else:
                                # LLM missed this interaction entirely
                                evidence_recall = 0.0
                            
                            movie_stats[movie_name]['evidence_recall_sum'] += evidence_recall
                            movie_stats[movie_name]['evidence_count'] += 1
                        else:
                            # If GT has no evidence lines listed, we skip evidence scoring for this item
                            pass

    # ==========================================
    # PRINT RESULTS
    # ==========================================

    print("\n" + "="*90)
    print(f"{'MOVIE':<30} | {'RELATIONSHIP ACCURACY':<25} | {'EVIDENCE RECALL (Line Match)':<25}")
    print("="*90)

    grand_total_rel = 0
    grand_correct_rel = 0
    grand_recall_sum = 0
    grand_recall_count = 0

    for movie, stats in movie_stats.items():
        # Rel Accuracy
        if stats['total_rel'] > 0:
            rel_acc = (stats['correct_rel'] / stats['total_rel']) * 100
        else:
            rel_acc = 0.0
            
        # Evidence Recall
        if stats['evidence_count'] > 0:
            avg_recall = (stats['evidence_recall_sum'] / stats['evidence_count']) * 100
        else:
            avg_recall = 0.0

        print(f"{movie:<30} | {rel_acc:6.2f}% ({stats['correct_rel']}/{stats['total_rel']})       | {avg_recall:6.2f}% (Avg. coverage of GT lines)")

        # Aggregate totals
        grand_total_rel += stats['total_rel']
        grand_correct_rel += stats['correct_rel']
        grand_recall_sum += stats['evidence_recall_sum']
        grand_recall_count += stats['evidence_count']

    print("="*90)
    
    # Overall
    if grand_total_rel > 0:
        overall_rel_acc = (grand_correct_rel / grand_total_rel) * 100
    else:
        overall_rel_acc = 0.0
        
    if grand_recall_count > 0:
        overall_recall = (grand_recall_sum / grand_recall_count) * 100
    else:
        overall_recall = 0.0

    print(f"{'OVERALL':<30} | {overall_rel_acc:6.2f}%                        | {overall_recall:6.2f}%")
    print("="*90)
    print(f"Total Files Processed: {total_files_processed}")
    print("\n* Evidence Recall explanation: If GT requires lines [1,2,3] and LLM provides [1,5], score is 33% (1/3).")
    print("  Extra lines found by LLM (e.g. line 5) are NOT penalized.")

if __name__ == "__main__":
    main()