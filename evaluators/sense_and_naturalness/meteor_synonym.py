from multiprocessing import Pool, cpu_count, freeze_support
from functools import lru_cache
from tqdm import tqdm
from ufal.udpipe import Model, Pipeline
import requests
from bs4 import BeautifulSoup


# Cache synonyms to avoid redundant HTTP requests
@lru_cache(maxsize=10000)
def get_synonyms(word):
    url = f"http://www.potafocal.com/thes/?s={word}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return set()  # Return an empty set if the word is not found

    soup = BeautifulSoup(response.text, "html.parser")
    synonyms_sections = soup.find_all("div", class_="sense")

    entries = []
    if synonyms_sections:
        for section in synonyms_sections:
            if section:
                synonyms = [a.text.strip() for a in section.find_all("a", href=True)]
                entries += synonyms

    return set(entries)


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
    for i in range(len(hypothesis)):
        if hypothesis[i] in reference:
            if not in_chunk:
                chunks += 1
                in_chunk = True
        else:
            in_chunk = False
    return chunks


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
    ref_tokens, ref_lemmas = extract_tokens_and_lemmas(ref_output)
    hyp_tokens, hyp_lemmas = extract_tokens_and_lemmas(hyp_output)

    # Use lemmas for matching
    matches = 0
    for lemma in set(ref_lemmas).intersection(hyp_lemmas):
        matches += 1

    # Include synonym matches if a custom synonym function is provided
    if get_synonyms:
        # Create a set of all synonyms for the reference words
        ref_synonyms = set()
        for ref_word in ref_lemmas:
            ref_synonyms.update(get_synonyms(ref_word))

        # Check if any hypothesis word is in the synonym set
        for hyp_word in hyp_lemmas:
            if hyp_word in ref_synonyms:
                matches += 1

    # Calculate precision, recall, and F-measure
    precision = matches / len(hyp_lemmas) if len(hyp_lemmas) > 0 else 0
    recall = matches / len(ref_lemmas) if len(ref_lemmas) > 0 else 0
    f_score = (precision * recall) / (alpha * precision + (1 - alpha) * recall) if (precision + recall) > 0 else 0

    # Calculate fragmentation penalty
    chunks = calculate_chunks(ref_lemmas, hyp_lemmas)
    frag_penalty = gamma * (chunks / matches) ** beta if matches > 1 else 0

    # Calculate final METEOR score
    meteor_score = max(f_score * (1 - frag_penalty), 0)
    return meteor_score


def process_sentence_pair(args):
    ref, hyp, get_synonyms = args
    model = Model.load("irish-idt-ud-2.5-191206.udpipe")
    if not model:
        print("Error: Could not load the UDPipe model.")
        exit(1)
    # Create a pipeline for tokenization and lemmatization
    pipeline = Pipeline(model, "tokenize", Pipeline.DEFAULT, Pipeline.DEFAULT, "conllu")

    # Compute METEOR score
    score = my_meteor_score(ref, hyp, pipeline, get_synonyms)
    return score


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


if __name__ == '__main__':
    freeze_support()  # Required for Windows and macOS

    # Load and process sentences
    references = []
    hypotheses = []
    with open("ga_txt_files/references.txt", "r", encoding="utf-8") as f, open("ga_txt_files/nllbs.txt", "r", encoding="utf-8") as f2:
        for ref_line, test_line in zip(f, f2):
            references.append(ref_line.strip())
            hypotheses.append(test_line.strip())

    # Use multiprocessing to calculate scores in parallel
    with Pool(cpu_count()) as pool:
        # Wrap pool.map with tqdm for a progress bar
        meteor_scores = list(tqdm(
            pool.imap(process_sentence_pair, [(ref, hyp, get_synonyms) for ref, hyp in zip(references, hypotheses)]),
            total=len(references),  # Total number of iterations
            desc="Calculating METEOR scores",  # Progress bar description
            unit="sentence"  # Unit of progress
        ))

    # Calculate the average METEOR score
    average_meteor = sum(meteor_scores) / len(meteor_scores)
    print("Average METEOR score:", average_meteor)
