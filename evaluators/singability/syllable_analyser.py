import pronouncing
import textstat
import requests
import urllib.parse
import json
import os

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


# Get syllable count for sentence
def syllabize_sentence(sentence, language, cache=None):
    words = sentence.split()
    if language == "en":
        return sum(syllabize_word_en(word) for word in words)
    else:
        return syllabize_sentence_ga(sentence, cache)


# Counting syllables of input English word using Pronouncing
def syllabize_word_en(word):
    phones = pronouncing.phones_for_word(word)  # Lowercase for CMU dictionary
    if phones:
        return pronouncing.syllable_count(phones[0])
    else:
        return syllabize_word_en_fallback(word)  # Fallback to textstat


# Fallback function using textstat if Pronouncing fails
def syllabize_word_en_fallback(word):
    count = textstat.syllable_count(word)
    return count if count else 1  # Default to 1 if all else fails


# Counting syllables of input Irish sentence using Abair
def syllabize_sentence_ga(sentence, cache):
    phonetised_sen = phonetise_text(sentence, cache)
    syllables = sum([word.count(".") + 1 for word in phonetised_sen])
    return syllables


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

    og_songs = split_into_songs([line.strip() for line in originals])
    hyp_songs = split_into_songs([line.strip() for line in hypotheses])

    for i, (og_song, hyp_song) in enumerate(zip(og_songs, hyp_songs)):
        differences = []
        for og_sen, hyp_sen in zip(og_song, hyp_song):
            count_og = syllabize_sentence(og_sen, 'en')
            count_hyp = syllabize_sentence(hyp_sen, 'ga', cache)
            differences.append(abs(count_og - count_hyp)/count_og)
        song_objects[i]["syllable_diff"] = sum(differences)/len(differences)

    with open("results_by_song/reference.json", "w", encoding="utf-8") as file:
        json.dump(song_objects, file, indent=4, ensure_ascii=False)
