import gc
import json
import os
import torch
from bert_score import score
from transformers import AutoTokenizer
from joblib import Parallel, delayed
from tqdm import tqdm  # Import tqdm for progress bar

# Load tokenizer and model globally to avoid loading them multiple times
tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")

def split_into_songs(lines):
    songs = []
    current_song = []
    for line in lines:
        if "*" in line.strip():
            if current_song:
                songs.append(current_song)
                current_song = []
        else:
            current_song.append(line.strip())
    if current_song:
        songs.append(current_song)
    return songs


def compute_bertscore(ref_song, test_song):
    scores = []
    for ref_sen, test_sen in zip(ref_song, test_song):
        with torch.no_grad():
            _, _, F1 = score([ref_sen], [test_sen], lang="ga", model_type="xlm-roberta-base", verbose=False, device=torch.device('cpu'))
        scores.append(F1.item())
    clear_memory()
    return sum(scores) / len(scores)


def clear_memory():
    gc.collect()  # Collect garbage to free memory
    torch.cuda.empty_cache()  # If using CUDA, clear the GPU cache (if applicable)


if __name__ == "__main__":
    # Read reference and hypothesis files
    with open("ga_txt_files/references.txt", "r", encoding="utf-8") as f:
        references = f.readlines()

    with open("ga_txt_files/nllbs.txt", "r", encoding="utf-8") as f:
        hypotheses = f.readlines()

    # Ensure JSON file exists
    json_path = "results_by_song/nllb.json"
    if os.path.exists(json_path) and os.path.getsize(json_path) > 0:
        with open(json_path, "r", encoding="utf-8") as file:
            try:
                song_objects = json.load(file)
            except json.JSONDecodeError:
                print(f"Error: {json_path} is not valid. Resetting it.")
                song_objects = []
    else:
        song_objects = []

    # Split into songs
    ref_songs = split_into_songs(references)
    test_songs = split_into_songs(hypotheses)

    if len(ref_songs) != len(test_songs):
        raise ValueError(f"Mismatch in song count: {len(ref_songs)} references vs {len(test_songs)} hypotheses")

    # Process each song in parallel and collect results
    results = Parallel(n_jobs=10)(
        delayed(compute_bertscore)(ref_song, test_song)
        for ref_song, test_song in tqdm(zip(ref_songs, test_songs), total=len(ref_songs), desc="Processing Songs")
    )

    # Update song_objects with results
    for i, result in enumerate(results):
        song_objects[i]["bert_score"] = result  # Ensure consistent key usage

    # Save updated results to JSON file
    with open("results_by_song/nllb1.json", "w", encoding="utf-8") as file:
        json.dump(song_objects, file, indent=4, ensure_ascii=False)

    clear_memory()
