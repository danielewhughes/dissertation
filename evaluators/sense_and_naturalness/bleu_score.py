from sacrebleu.metrics import BLEU, CHRF

# Load hypothesis translations (machine-generated)
with open("ga_txt_files/googles.txt", "r", encoding="utf-8") as f:
    test_lines = [line.strip() for line in f.readlines()]


# Load reference translations
with open("ga_txt_files/references.txt", "r", encoding="utf-8") as f:
    references = [line.strip() for line in f.readlines()]

# sacreBLEU expects a list of reference lists (even for a single reference)
references_list = [references]

# Compute BLEU score
bleu = BLEU()
score = bleu.corpus_score(test_lines, references_list)
#print(bleu.get_signature())
print(f"{score}")

chrf = CHRF()
score_2 = chrf.corpus_score(test_lines, references_list)
print(f"{score_2}")
