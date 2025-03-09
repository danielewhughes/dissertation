from ufal.udpipe import Model, Pipeline
import nltk
import json
from nltk.translate import meteor_score
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet as wn


with open("ga_txt_files/references.txt", "r", encoding="utf-8") as f:
    references = f.readlines()

with open("ga_txt_files/nllbs.txt", "r", encoding="utf-8") as f:
    hypotheses = f.readlines()

with open("results_by_song/nllb.json", "r", encoding="utf-8") as file:
        song_objects = json.load(file)

# Function to split lines into songs based on the "*" delimiter
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


# Split references and test_lines into songs
ref_songs = split_into_songs(references)
test_songs = split_into_songs(hypotheses)

### Using UDPipe tokeniser
model_path = "irish-idt-ud-2.5-191206.udpipe"  # Path to the downloaded model
model = Model.load(model_path)
if not model:
    print("Error: Could not load the UDPipe model.")
    exit(1)

pipeline = Pipeline(model, "tokenize", Pipeline.DEFAULT, Pipeline.DEFAULT, "conllu")


def extract_tokens(conllu_output):
    tokens = []
    for line in conllu_output.splitlines():
        if line and not line.startswith("#"):
            columns = line.split("\t")
            if len(columns) > 1:
                tokens.append(columns[1])  # FORM is in the second column
    return tokens


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


for i, (ref_song, hyp_song) in enumerate(zip(ref_songs, test_songs)):
    meteor_scores = []
    for line1, line2 in zip(ref_song, hyp_song):
        _, lemma_ref = extract_tokens_and_lemmas(pipeline.process(line1))
        _, lemma_test = extract_tokens_and_lemmas(pipeline.process(line2))
        score = meteor_score.meteor_score([lemma_ref], lemma_test)
        meteor_scores.append(score)
    # Calculate the songs METEOR score
    average_meteor = sum(meteor_scores) / len(meteor_scores) if meteor_scores else 0
    song_objects[i]["meteor"] = average_meteor


### Using nltk tokeniser ###
"""
for i, song in enumerate(ref_songs):
    song_object = song_objects[i]
    # Tokenize the sentences
    tokenised_refs = [word_tokenize(line.strip()) for line in song]
    tokenised_tests = [word_tokenize(line2.strip()) for line2 in test_songs[i]]
    # Calculate METEOR score for each sentence pair
    meteor_scores = []
    for ref, hyp in zip(tokenised_refs, tokenised_tests):
        score = meteor_score.meteor_score([ref], hyp)
        meteor_scores.append(score)
    average_meteor = sum(meteor_scores)/len(meteor_scores)
    song_object["meteor"] = average_meteor
    song_objects[i] = song_object
"""

with open("results_by_song/nllb1.json", "w", encoding="utf-8") as file:
    json.dump(song_objects, file, indent=4, ensure_ascii=False)
