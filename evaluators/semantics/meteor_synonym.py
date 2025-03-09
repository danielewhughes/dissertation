from multiprocessing import Pool, cpu_count, freeze_support
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from tqdm import tqdm
from ufal.udpipe import Model, Pipeline
import requests
from bs4 import BeautifulSoup
import json
import os

SYNONYM_CACHE_FILE = "ga_txt_files/synonyms_cache.json"
synonym_cache = {}

# Load cached synonyms to avoid redundant HTTP requests
def load_synonym_cache():
    global synonym_cache
    if os.path.exists(SYNONYM_CACHE_FILE) and os.path.getsize(SYNONYM_CACHE_FILE) > 0:
        with open(SYNONYM_CACHE_FILE, "r", encoding="utf-8") as f:
            try:
                loaded_cache = json.load(f)
                synonym_cache = {key: set(value) for key, value in loaded_cache.items()}
            except json.JSONDecodeError:
                print("Warning: Invalid JSON in synonym cache. Resetting cache.")
                synonym_cache = {}
    else:
        synonym_cache = {}


def save_synonym_cache():
    with open(SYNONYM_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({key: list(value) for key, value in synonym_cache.items()}, f, ensure_ascii=False, indent=4)


# Fetch synonyms for a batch of words
def fetch_synonyms_batch(words, pipeline):
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_synonyms, words, [pipeline]*len(words)))
    return dict(zip(words, results))


# Fetch synonyms from Potafocal
def fetch_synonyms(word, pipeline):
    if word in synonym_cache:
        return synonym_cache[word]
    
    url = f"http://www.potafocal.com/thes/?s={word}"
    response = requests.get(url)
    if response.status_code != 200:
        return set()  # Return an empty set, not a list

    soup = BeautifulSoup(response.text, "html.parser")
    synonyms = {a.text.strip().lower() for section in soup.find_all("div", class_="sense") for a in section.find_all("a", href=True)}
    syn_lemmas = []
    for synonym in synonyms:
        _, syn_lemma = extract_tokens_and_lemmas(pipeline.process(synonym))
        syn_lemmas += syn_lemma
    synonym_cache[word] = set(syn_lemmas)  # Store as a set to avoid list issues
    return set(syn_lemmas)  # Ensure return value is a set


# Get synonyms from cache
def get_synonyms(word):
    return set(synonym_cache.get(word, []))  # Ensure it returns a set


# Preload synonyms for words in references
def preload_synonyms(word_list, pipeline):
    new_words = [word for word in word_list if word not in synonym_cache]
    if new_words:
        synonym_cache.update(fetch_synonyms_batch(new_words, pipeline))
        save_synonym_cache()


# UDPipe lemmatization using parallel processing
def process_with_pipeline(text, pipeline):
    return pipeline.process(text.strip())


def lemmatize_sentences_parallel(sentences, pipeline):
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        return list(executor.map(lambda text: process_with_pipeline(text, pipeline), sentences))


def extract_tokens_and_lemmas(conllu_output):
    """
    Extract tokens and lemmas from CoNLL-U format output.
    
    :param conllu_output: CoNLL-U format string.
    :return: A tuple of (tokens, lemmas).
    """
    tokens = []
    lemmas = []
    for line in conllu_output.splitlines():
        if line and not line.startswith("#"):
            columns = line.split("\t")
            if len(columns) > 2:  # Ensure the line has enough columns
                tokens.append(columns[1])  # FORM is in the 2nd column
                lemmas.append(columns[2])  # LEMMA is in the 3rd column
    return tokens, lemmas


# Calculate chunks for METEOR
def calculate_chunks(reference, hypothesis):
    """
    Calculate the number of contiguous matching chunks between reference and hypothesis.
    
    :param reference: List of reference tokens.
    :param hypothesis: List of hypothesis tokens.
    :return: Number of chunks.
    """
    if not reference or not hypothesis:
        return 0

    chunks = 0
    in_chunk = False
    for i, _ in enumerate(hypothesis):
        if hypothesis[i] in reference:
            if not in_chunk:
                chunks += 1
                in_chunk = True
        else:
            in_chunk = False
    return chunks


# Compute METEOR Score
def my_meteor_score(
    reference,
    hypothesis,
    pipeline,
    get_synonyms=None,  # Custom synonym function
    alpha=0.9,
    beta=3,
    gamma=0.5,
):
    """
    Calculate the METEOR score with custom synonym support.
    
    :param reference: Reference sentence (string).
    :param hypothesis: Hypothesis sentence (string).
    :param pipeline: UDPipe pipeline for lemmatization.
    :param get_synonyms: Function to get synonyms for a word.
    :param alpha: Parameter for precision vs. recall weighting.
    :param beta: Parameter for fragmentation penalty.
    :param gamma: Parameter for chunk penalty.
    :return: METEOR score.
    """
    # Lemmatize the reference and hypothesis sentences
    ref_output = pipeline.process(reference.strip())
    hyp_output = pipeline.process(hypothesis.strip())
    _, ref_lemmas = extract_tokens_and_lemmas(ref_output)
    _, hyp_lemmas = extract_tokens_and_lemmas(hyp_output)

    # Initialize matches
    matches_set = set()

    # Exact word matches
    for hyp_word in hyp_lemmas:
        if hyp_word in ref_lemmas and hyp_word not in matches_set:
            matches_set.add(hyp_word)

    # Include synonym matches if a custom synonym function is provided
    if get_synonyms:
        # Create a set of all synonyms for the reference words
        ref_synonyms = set()
        for ref_word in ref_lemmas:
            ref_synonyms.update(get_synonyms(ref_word))

        # Check if any hypothesis word is in the synonym set
        for hyp_word in hyp_lemmas:
            if hyp_word in ref_synonyms and hyp_word not in matches_set:
                matches_set.add(hyp_word)

    # Total matches are the size of the matches set
    matches = len(matches_set)

    # Calculate precision, recall, and F-measure
    precision = matches / len(hyp_lemmas) if len(hyp_lemmas) > 0 else 0
    recall = matches / len(ref_lemmas) if len(ref_lemmas) > 0 else 0

    # Calculate F-score
    f_score = (precision * recall) / (alpha * precision + (1 - alpha) * recall) if (precision + recall) > 0 else 0

    # Calculate fragmentation penalty (based on chunking)
    chunks = calculate_chunks(ref_lemmas, hyp_lemmas)
    frag_penalty = gamma * (chunks / matches) ** beta if matches > 1 else 0

    # Calculate final METEOR score
    meteor_score = max(f_score * (1 - frag_penalty), 0)
    return meteor_score



# Process sentence pairs
def process_sentence_pair(args):
    reference, hypothesis, pipeline, get_synonyms = args
    return my_meteor_score(reference, hypothesis, pipeline, get_synonyms)


# Split text into songs
def split_into_songs(lines):
    songs = []
    current_song = []
    for line in lines:
        if "*" in line:
            if current_song:
                songs.append(current_song)
                current_song = []
        else:
            current_song.append(line)
    if current_song:
        songs.append(current_song)
    return songs


if __name__ == '__main__':
    freeze_support()
    
    model = Model.load("irish-idt-ud-2.5-191206.udpipe")
    if not model:
        print("Error: Could not load UDPipe model.")
        exit(1)
    pipeline = Pipeline(model, "tokenize", Pipeline.DEFAULT, Pipeline.DEFAULT, "conllu")
    
    load_synonym_cache()

    json_path = "results_by_song/nllb.json"
    if os.path.exists(json_path) and os.path.getsize(json_path) > 0:
        with open(json_path, "r", encoding="utf-8") as file:
            try:
                song_objects = json.load(file)
            except json.JSONDecodeError:
                print("Error: google.json is not valid. Resetting it.")
                song_objects = []
    else:
        song_objects = []
    
    with open("ga_txt_files/references.txt", "r", encoding="utf-8") as f, open("ga_txt_files/nllbs.txt", "r", encoding="utf-8") as f2:
        references = [line.strip() for line in f]
        hypotheses = [line.strip() for line in f2]
    
    ref_songs, test_songs = split_into_songs(references), split_into_songs(hypotheses)
    all_ref_words = list(set(word for song in ref_songs for line in song for word in line.split()))
    preload_synonyms(all_ref_words, pipeline)

    song_scores = []
    for ref_song, hyp_song in zip(ref_songs, test_songs):
        with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            song_results = list(executor.map(process_sentence_pair, [(ref, hyp, pipeline, get_synonyms) for ref, hyp in zip(ref_song, hyp_song)]))

        avg_score = sum(song_results) / len(song_results) if song_results else 0
        song_scores.append(avg_score)  # Store the average score per song

        print("song processed")

    for i, score in enumerate(song_scores):
        song_objects[i]["meteor_synonym"] = score
    
    with open("results_by_song/nllb1.json", "w", encoding="utf-8") as file:
        json.dump(song_objects, file, indent=4, ensure_ascii=False)
    
    save_synonym_cache()