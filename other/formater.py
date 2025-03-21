import json
import re


def clean_lyrics(text):
    """Cleans lyrics by removing punctuation (except newlines) and lyric annotations."""
    # Remove lyric annotations like 'Chorus', 'Curfá', 'Séist' (case insensitive, full-line only)
    text = re.sub(r"(?i)\b(chorus|coro)\b", "", text, flags=re.MULTILINE)
    
    # Remove repetition indicators like 'x2', '3x' (case insensitive)
    text = re.sub(r"(?i)\b(\d+x|x\d+)\b", "", text)

    # Remove punctuation except newlines and spaces
    text = re.sub(r"[^\w\s]", "", text)

    # Remove paragrapgh breaks
    text = re.sub(r"\n\n", "\n", text)

    # Split text by newlines to process each line
    lines = text.split("\n")
    
    #cleaned_lines = []
    #for i, line in enumerate(lines):
    #    stripped_line = line.strip()

        # If the line is not empty or if it is an empty line following non-empty ones (for stanza breaks)
    #    if stripped_line or (i > 0 and not lines[i-1].strip()):
    #        cleaned_lines.append(stripped_line)

    # Join the cleaned lines, ensuring that we only have two newlines between stanzas
    #cleaned_text = "\n".join(cleaned_lines)

    # Convert extra newlines to stanza break
    #text = re.sub(r"\n{3,}", "\n\n", text.strip())
    cleaned_lines = [line.strip().lower() for line in lines]  # Trim spaces but keep empty lines

    return "\n".join(cleaned_lines)

def process_songs(input_file, output_file):
    """Reads JSON file, cleans lyrics, and writes cleaned data to a new file."""
    with open(input_file, "r", encoding="utf-8") as file:
        songs = json.load(file)

    lines = []
    with open(output_file, "w", encoding="utf-8") as file:
        for song in songs:
            file.write(song["deepl-translation"] + "\n*\n")

# Example usage
process_songs("data_files/en-es.json", "data_files/cleaned_songs.json")
