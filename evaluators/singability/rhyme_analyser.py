#1 Identify rhyme scheme of English song
#2 Label where rhymes occur
#3 Check syllables of Irish song

from collections import defaultdict
import re
import urllib.parse
import json
import os
import difflib
import pronouncing
import requests


# Cache file path of all Irish sentences with phonetic transcriptions
CACHE_FILE = "rhyme_files/phonetics_cache.json"
# Load cache from file if it exists
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)
else:
    cache = {}

VOWELS = "aeiou@"


def get_rhyme_part_english(word):
    """Get the last stressed syllable and onward from the word's phonetic transcription."""
    rhyme_parts = []
    #rhyme_part = None
    pronunciations = pronouncing.phones_for_word(word)
    if pronunciations:
        for pronunciation in pronunciations:
            phonemes = pronunciation.split(" ")
            """Loop through the list of phonemes in reverse and return the index of the first stressed vowel."""
            for i in range(len(phonemes) - 1, -1, -1):  # Loop in reverse using index
                phoneme = phonemes[i]
                if phoneme[-1] in "12" and phoneme[0] in "AEIOU":  # Check for stress (1 or 2) and vowel
                    rhyme_part = " ".join(phonemes[i:])  # Join the phonemes to form a string
                    rhyme_parts.append(rhyme_part)  # Return the index of the first stressed vowel
                    break
    return rhyme_parts


def get_rhyme_part_irish(word):
    """Extracts the last stressed vowel and all following phonemes from a word."""
    phonemes = None
    if word in cache:
        phonemes = cache[word]
    else:
        # Call API
        base_url = "https://synthesis.abair.ie/api/phonetise"
        encoded_text = urllib.parse.quote(word)
        url = f"{base_url}?text={encoded_text}&dialect={'co'}&mapping={'mrpai'}&add_origins={'false'}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                result = response.json()
                
                # Check if result is a list and not empty
                if result and isinstance(result, list):
                    phonemes = result[0]  # Get the first item if it exists
                    # Save result to cache
                    cache[word] = phonemes
                    # Save cache to file
                    with open(CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump(cache, f, ensure_ascii=False, indent=4)
                else:
                    print(f"Error: No valid phoneme data returned for word: {word}")
                    return "?"
            else:
                print(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")

    # Find last stressed syllable
    index = phonemes.rfind('1')
    # Find stressed vowel and following phonemes
    for i in range(index, len(phonemes)):
        if phonemes[i] in VOWELS:
            return phonemes[i:]


def get_rhyme_scheme(stansa, lang):
    """Detects the rhyme scheme of given lyrics."""
    lines = stansa.strip().split("\n")
    rhyme_map = {}
    rhyme_scheme = []
    next_label = 'A'
    rhyme_parts = []
    end_phonemes = []

    for line in lines:
        words = line.split()
        last_word = words[-1]
        if lang == "en":
            rhyme_parts = get_rhyme_part_english(last_word)
        else:
            rhyme_parts = [get_rhyme_part_irish(last_word)]
        end_phonemes.append(rhyme_parts)

        # Check for perfect rhyme match first
        rhyme_label = None
        for rhyme_part in rhyme_parts:
            if rhyme_part in rhyme_map:
                rhyme_label = rhyme_map[rhyme_part]
                break
        
        # Assign a new label if no match has been found
        if rhyme_label is None:
            rhyme_label = next_label
            for rhyme_part in rhyme_parts:
                rhyme_map[rhyme_part] = rhyme_label
            next_label = chr(ord(next_label) + 1)  # Move to next letter

        rhyme_scheme.append(rhyme_label)
       
    # Second pass: Update rhyme scheme to reflect slant rhymes
    for indexx, _ in enumerate(rhyme_scheme):
        for x, _ in enumerate(rhyme_scheme):
            if rhyme_scheme.count(rhyme_scheme[x]) > 1 or rhyme_scheme[x].islower():  # If it's a lowercase label (slant rhyme)
                continue  # No update needed for already slant rhymes
            if indexx == x:
                continue
            # Compare line i and line j for slant rhyme
            similarity = 0
            for pronounciation in end_phonemes[indexx]:
                for pronounciation2 in end_phonemes[x]:
                    similarity = max(similarity, difflib.SequenceMatcher(None, pronounciation, pronounciation2).ratio())
            if similarity > 0.7:  # Adjust threshold as needed for slant rhyme matching
                # If a slant rhyme is found, update line j's label to the same as line i
                rhyme_scheme[x] = rhyme_scheme[indexx].lower()  # Lowercase to signify slant rhyme
                if rhyme_scheme.count(rhyme_scheme[indexx]) == 1:
                    rhyme_scheme[indexx] = rhyme_scheme[indexx].lower()
                break

    return "".join(rhyme_scheme)


def check_perfect_match(ref, test):
    index_map_ref = {}
    for index, char in enumerate(ref):
        if index_map_ref.get(char):
            index_map_ref[char].append(index)
        else:
            index_map_ref[char] = [index]
    index_map_test = {}
    for x, ch in enumerate(test):
        if index_map_test.get(ch):
            index_map_test[ch].append(x)
        else:
            index_map_test[ch] = [x]
    
    for indices in index_map_ref.values():
        if len(indices) > 1 and ref[indices[0]].isupper():
            if indices not in index_map_test.values():
                return False
            if ref[indices[0]].isupper() and test[indices[0]].islower():
                return False
            if ref[indices[0]].islower() and test[indices[0]].isupper():
                return False
            
    return True


def check_good_match(ref, test):
    index_map_ref = {}
    for index, char in enumerate(ref):
        if index_map_ref.get(char):
            index_map_ref[char].append(index)
        else:
            index_map_ref[char] = [index]
    index_map_test = {}
    for x, ch in enumerate(test):
        if index_map_test.get(ch):
            index_map_test[ch].append(x)
        else:
            index_map_test[ch] = [x]
    
    for indices in index_map_ref.values():
        if len(indices) > 1:
            if indices not in index_map_test.values():
                return False
            
    return True


def check_partial_match(ref, test):
    index_map_ref = {}
    for index, char in enumerate(ref):
        if index_map_ref.get(char):
            index_map_ref[char].append(index)
        else:
            index_map_ref[char] = [index]
    index_map_test = {}
    for x, ch in enumerate(test):
        if index_map_test.get(ch):
            index_map_test[ch].append(x)
        else:
            index_map_test[ch] = [x]
    
    for indices in index_map_ref.values():
        if len(indices) > 1:
            if indices in index_map_test.values():
                return True
            
    return False


if __name__ == '__main__':

    # Step 1: Open and read the file
    with open('rhyme_files/originals.txt', 'r', encoding='utf-8') as file1, open('rhyme_files/references.txt', 'r', encoding='utf-8') as file2:
        references = file1.read()
        hypotheses = file2.read()
    # Step 2: Split the content by the '*' delimiter
    ref_songs = references.split('*')
    hyp_songs = hypotheses.split('*')

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

    # Step 3: Process each song
    for i, (og_song, hyp_song) in enumerate(zip(ref_songs, hyp_songs)):
        ref_stanzas = re.split(r"\n\s*\n", og_song)
        hyp_stanzas = re.split(r"\n\s*\n", hyp_song)

        # Song score
        score = 0
        rhyme_count = 0

        # Get rhyme schemes
        for j, (ref_stanza, hyp_stanza) in enumerate(zip(ref_stanzas, hyp_stanzas)):
            ref_rhyme_scheme = get_rhyme_scheme(ref_stanza, "en")
            hyp_rhyme_scheme = get_rhyme_scheme(hyp_stanza, "ga")

            # If no rhyme in original, skip
            if len(ref_stanza) == len(set(ref_stanza)):
                continue

            rhyme_count += 1

            if ref_rhyme_scheme == hyp_rhyme_scheme:
                score += 1
                continue
            if check_perfect_match(ref_rhyme_scheme, hyp_rhyme_scheme):
                score += 0.8
                continue
            if check_good_match(ref_rhyme_scheme, hyp_rhyme_scheme):
                score += 0.6
                continue
            if check_partial_match(ref_rhyme_scheme, hyp_rhyme_scheme):
                score += 0.4

        if rhyme_count == 0:
            song_objects[i]["rhyme_diff"] = 0
        else:
            song_objects[i]["rhyme_diff"] =  1 - (score/rhyme_count)

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(song_objects, file, indent=4, ensure_ascii=False)
