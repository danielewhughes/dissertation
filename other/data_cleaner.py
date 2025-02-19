import json
import re

def clean_and_align_lyrics(input_file, output_file):
    # Load the JSON data
    with open(input_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Helper function to clean lyrics
    def clean_lyrics(lyrics):
        # Split the text into lines to preserve newline characters
        lines = lyrics.split('\n')
        
        # Clean each line independently
        cleaned_lines = []
        for line in lines:
            # Remove annotations like [Intro], [Verse], [Chorus], [4x], etc.
            line = re.sub(r'\[.*?\]', '', line)
            # Remove special characters and repeated punctuation
            line = re.sub(r'\.{2,}', '', line)  # Remove ellipses ("...")
            line = re.sub(r'[-–—]', '', line)  # Remove dashes
            line = re.sub(r'\s{2,}', ' ', line)  # Replace multiple spaces with one
            line = re.sub(r'[\(\)]', '', line)  # Remove parentheses
            line = re.sub(r'[^\w\s\.,!?\'\"-]', '', line)  # Remove unwanted special characters
            cleaned_lines.append(line.strip())  # Add cleaned line to the list

        # Join the cleaned lines back together with newline characters
        return '\n'.join(cleaned_lines)

    cleaned_data = []
    for entry in data:
        datet = {}
        original = entry.get('original-lyrics', '').strip()
        translated = entry.get('translated-lyrics', '').strip()

        # Clean both original and translated lyrics
        original_cleaned = clean_lyrics(original)
        translated_cleaned = clean_lyrics(translated)

        datet["title"] = entry["title"]
        datet["original-lyrics"] = original_cleaned
        datet["translated-lyrics"] = translated_cleaned
        cleaned_data.append(datet)


    # Save to output file
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(cleaned_data, file, indent=4, ensure_ascii=False)

    print(f"Cleaned and aligned lyrics saved to {output_file}")
    print(f"{len(cleaned_data)}")

# Usage
input_file = 'en-es.json'  # Replace with the path to your input file
output_file = 'en-es-new.json'  # Replace with desired output file name
clean_and_align_lyrics(input_file, output_file)
