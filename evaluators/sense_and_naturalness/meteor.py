# from ufal.udpipe import Model, Pipeline
import nltk
from nltk.translate import meteor_score
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet as wn


with open("ga_txt_files/references.txt", "r", encoding="utf-8") as f:
    references = f.readlines()

with open("ga_txt_files/nllbs.txt", "r", encoding="utf-8") as f:
    hypotheses = f.readlines()

"""

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

meteor_scores = []
for ref, test in zip(references, hypotheses):
    tokenised_ref = extract_tokens(pipeline.process(ref))
    tokenised_test = extract_tokens(pipeline.process(test))
    score = meteor_score.meteor_score([tokenised_ref], tokenised_test)
    meteor_scores.append(score)

average_meteor = sum(meteor_scores) / len(meteor_scores)
print(average_meteor)

"""


### Using nltk tokeniser ###
    
# Tokenize the sentences
tokenised_refs = [word_tokenize(ref.strip()) for ref in references]
tokenised_tests = [word_tokenize(hyp.strip()) for hyp in hypotheses]

# Calculate METEOR score for each sentence pair
meteor_scores = []
for ref, hyp in zip(tokenised_refs, tokenised_tests):
    score = meteor_score.meteor_score([ref], hyp)
    print(score)
    meteor_scores.append(score)

# Calculate the average METEOR score
average_meteor = sum(meteor_scores) / len(meteor_scores)
print(average_meteor)

