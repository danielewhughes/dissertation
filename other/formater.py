import json
import re

with open("/Users/danielhughes/Documents/College/Fourth-Year/Capstone/Dissertation/data_files/en-ga.json", "r", encoding="utf-8") as f:
    songs = json.load(f)

references = []
originals = []
googles = []
nllbs = []

for song in songs:
    references.append(song.get("translated-lyrics", ""))
    originals.append(song.get("original-lyrics", ""))
    googles.append(song.get("google-translation", ""))
    nllbs.append(song.get("nllb-200-translation", ""))

def normalize_text(text):
    text = re.sub(r"[^\w\s,']", "", text)
    text = re.sub(r"\s*(\d+x|x\d+)\s*", " ", text).strip()
    text = text.replace("\n\n", "\n")
    lines = text.lower().split("\n")  # Keep all lines
    cleaned_lines = [line.strip() for line in lines]  # Trim spaces but keep structure
    return "\n".join(cleaned_lines)


references = [normalize_text(line) for line in references]
originals = [normalize_text(line) for line in originals]
googles = [normalize_text(line) for line in googles]
nllbs = [normalize_text(line) for line in nllbs]

print("Processing complete!")

def write_to_file(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        for line in data:
            f.write(line + " ")


write_to_file("ga_txt_files/originals.txt", originals)
write_to_file("ga_txt_files/references.txt", references)
write_to_file("ga_txt_files/googles.txt", googles)
write_to_file("ga_txt_files/nllbs.txt", nllbs)

print("Files saved successfully!")
