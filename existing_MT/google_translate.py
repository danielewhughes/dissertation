import json
from google.cloud import translate_v2 as translate


def translate_text(target: str, texts: list) -> list:
    """Translates a list of texts into the target language."""
    
    translate_client = translate.Client()

    # Ensure all text is a string
    texts = [t.decode("utf-8") if isinstance(t, bytes) else t for t in texts]

    # Google Translate API supports batch translation
    results = translate_client.translate(texts, target_language=target)

    # Extract translations from response
    return [result["translatedText"] for result in results]


def main():
    # Load the JSON file
    with open("/Users/danielhughes/Documents/College/Fourth-Year/Capstone/Dissertation/data_files/en-es_trial.json", "r", encoding="utf-8") as f:
        songs = json.load(f)

    for song in songs:
        original_lyrics = song.get("original-lyrics", "")
        if original_lyrics:
            sentences = original_lyrics.split("\n")
            try:
                translated_sentences = translate_text("es", sentences)
                song["google-translation"] = "\n".join(translated_sentences)
            except Exception as e:
                print(f"Error translating song '{song.get('title', 'Unknown')}': {e}")

    with open("data_files/en-es_trial_2.json", "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()