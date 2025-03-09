import urllib.parse
import re
import json
import os
import requests
import pronouncing
import Levenshtein
from nltk.corpus import cmudict

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


# Get stress pattern for sentence
def phonetise_sentence(sentence, language, cache=None):
    if language == "en":
        return phonetise_sentence_en(sentence, cache)
    else:
        return phonetise_sentence_ga(sentence, cache)


# Get stress pattern English
def phonetise_sentence_en(sentence, cache):
    # Using pronouncing
    return get_stress_pattern_pronouncing(sentence, cache)


def get_stress_pattern_pronouncing(sentence, cache):
    words = sentence.split()
    pattern = []
    for word in words:
        if word in cache:
            return cache[word]
        pronunciation = pronouncing.phones_for_word(word)
        if pronunciation:
            # Get stress pattern of first pronunciation
            stress = pronouncing.stresses(pronunciation[0])
            pattern.append(stress)
        else:
            # Back up - use NLTK when pronouncing fails
            get_stress_pattern_nltk(word, cache)
    return "".join(pattern).replace(" ", "")


def get_stress_pattern_nltk(sentence, cache):
    d = cmudict.dict()
    words = sentence.split()
    pattern = []
    for word in words:
        if word in cache:
            return cache[word]
        if word in d:
            # Take first pronunciation
            syllables = d[word][0]
            # Extract stress digits (0, 1, or 2)
            stress = ''.join([char[-1] for char in syllables if char[-1].isdigit()])
            pattern.append(stress)
        else:
            pattern.append("?")  # Unknown word
    return "".join(pattern)


# Get stress pattern Irish 
def phonetise_sentence_ga(sentence, cache):
    phonetised_sen = phonetise_text(sentence, cache)
    stress_pattern = ""
    for pronunciation in phonetised_sen:
        stresses = re.sub(r"\D", "", pronunciation)
        stress_pattern += stresses
    return stress_pattern


def phonetise_text(text, cache, dialect="co", mapping="mrpai", add_origins="false"):
    """Phonetise text using Abair API, but only if it's not cached."""
    # Check cache first
    if text in cache:
        return cache[text]

    # If not cached, call API
    base_url = "https://synthesis.abair.ie/api/phonetise"
    encoded_text = urllib.parse.quote(text)
    url = f"{base_url}?text={encoded_text}&dialect={dialect}&mapping={mapping}&add_origins={add_origins}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            # Save result to cache
            cache[text] = result
            # Save cache to file
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=4)
            return result
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None


if __name__ == '__main__':
    # Cache file path of all Irish sentences with phonetic transcriptions
    CACHE_FILE = "singability_files/phonetics_cache.json"

    # Load cache from file if it exists
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
    else:
        cache = {}

    # Read reference and hypothesis files
    with open("ga_txt_files/originals.txt", "r", encoding="utf-8") as f:
        originals = f.readlines()

    with open("ga_txt_files/references.txt", "r", encoding="utf-8") as f:
        hypotheses = f.readlines()

    og_songs = split_into_songs([line.strip() for line in originals])
    hyp_songs = split_into_songs([line.strip() for line in hypotheses])
    
    # Ensure JSON file exists
    json_path = "results_by_song/reference.json"
    if os.path.exists(json_path) and os.path.getsize(json_path) > 0:
        with open(json_path, "r", encoding="utf-8") as file:
            try:
                song_objects = json.load(file)
            except json.JSONDecodeError:
                print(f"Error: {json_path} is not valid. Resetting it.")
                song_objects = []
    else:
        song_objects = []

    for i, (og_song, hyp_song) in enumerate(zip(og_songs, hyp_songs)):
        similarities = []
        for og_sen, hyp_sen in zip(og_song, hyp_song):
            stress_pat_og = phonetise_sentence(og_sen, "en", cache)
            stress_pat_hyp = phonetise_sentence(hyp_sen, "ga", cache)
            similarities.append(Levenshtein.ratio(stress_pat_og, stress_pat_hyp))
        song_objects[i]["stress_diff"] = 1 - (sum(similarities)/len(similarities))

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(song_objects, file, indent=4, ensure_ascii=False)
