import json
import deepl

# Your DeepL API key
DEEPL_API_KEY = "70fa71af-e618-48f5-ac43-05ee1e79016b:fx"
translator = deepl.Translator(DEEPL_API_KEY)    

def main():
    with open("data_files/en-es.json", "r", encoding="utf-8") as f:
        songs = json.load(f)

    for song in songs:
        original_lyrics = song.get("original-lyrics", "")
        if original_lyrics:
            stanzas = original_lyrics.split("\n\n")
            translated_stanzas = []  # Reset for each song

            for stanza in stanzas:
                translation = translator.translate_text(stanza, target_lang="ES")
                translated_stanzas.append(translation.text)  # Extract text

            song["deepl-translation"] = "\n\n".join(translated_stanzas)
            print(song["deepl-translation"])

    with open("en-es_trial.json", "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()