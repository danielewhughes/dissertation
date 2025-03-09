from sacrebleu.metrics import BLEU, CHRF
from tqdm import tqdm
from ufal.udpipe import Model, Pipeline
import json


def lemmatise(sentence, pipeline):
    sen_output = pipeline.process(sentence.strip())
    _ , sen_lemmas = extract_tokens_and_lemmas(sen_output)
    return " ".join(sen_lemmas)


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


# Function to split lines into songs based on the "*" delimiter
def split_into_songs(lines):
    songs = []
    current_song = []
    for line in lines:
        if line == "*":
            if current_song:
                songs.append(current_song)
                current_song = []
        else:
            current_song.append(line)
    if current_song:
        songs.append(current_song)
    return songs


if __name__ == '__main__':
    # Set up lemmatisesr
    model = Model.load("irish-idt-ud-2.5-191206.udpipe")
    if not model:
        print("Error: Could not load the UDPipe model.")
        exit(1)
    # Create a pipeline for tokenization and lemmatization
    pipeline = Pipeline(model, "tokenize", Pipeline.DEFAULT, Pipeline.DEFAULT, "conllu")

    # Load hypothesis translations (machine-generated)
    with open("ga_txt_files/nllbs.txt", "r", encoding="utf-8") as f: 
        # With lemmatisation
        test_lines = [lemmatise(line.strip(), pipeline) for line in f.readlines()]

    # Load reference translations
    with open("ga_txt_files/references.txt", "r", encoding="utf-8") as f:
        # With lemmatisation
        references = [lemmatise(line.strip(), pipeline) for line in f.readlines()]
    
    # Split references and test_lines into songs
    ref_songs = split_into_songs(references)
    test_songs = split_into_songs(test_lines)

    song_results = []
    # Compute BLEU score
    bleu = BLEU(effective_order=True)
    chrf = CHRF()
    for i, (ref_song, hyp_song) in enumerate(zip(ref_songs, test_songs)):
        song_object = {
            "index": i,
        }
        bleu_score = 0
        chrf_score = 0
        for j, (ref_line, hyp_line) in enumerate(zip(ref_song, hyp_song)):
            bleu_score += bleu.sentence_score(ref_line, hyp_line).score
            chrf_score += chrf.sentence_score(ref_line, hyp_line).score

        song_object["sacrebleu"] = bleu_score/len(ref_song)
        song_object["chrf"] = chrf_score/len(ref_song)

        song_results.append(song_object)

    with open("results_by_song/nllb.json", "w", encoding="utf-8") as file:
        json.dump(song_results, file, indent=4, ensure_ascii=False)
