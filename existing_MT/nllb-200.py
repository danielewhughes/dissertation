import json
#import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = "facebook/nllb-200-distilled-600M"

def main():
    # Load the JSON file
    with open("/Users/danielhughes/Documents/College/Fourth-Year/Capstone/Dissertation/data_files/en-es.json", "r", encoding="utf-8") as f:
        songs = json.load(f)

    # Load the tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

    # Get the target language ID
    lang_id = tokenizer.convert_tokens_to_ids("spa_Latn") #Irish


    BATCH_SIZE = 16  # Adjust batch size based on memory availability

    for i, song in enumerate(songs):    
        original_lyrics = song.get("original-lyrics", "")
        source_text = original_lyrics.split("\n")
    
        translated_lines = []
        for j in range(0, len(source_text), BATCH_SIZE):
            batch = source_text[j : j + BATCH_SIZE]
            inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True)
            outputs = model.generate(**inputs, max_length=512, forced_bos_token_id=lang_id)
            translated_batch = tokenizer.batch_decode(outputs, skip_special_tokens=True)
            translated_lines.extend(translated_batch)

        song["nllb-200-translation"] = "\n".join(translated_lines)
        print(song["nllb-200-translation"])
        print(f"processed: {i}")

    # Save the updated JSON file
    with open("/Users/danielhughes/Documents/College/Fourth-Year/Capstone/Dissertation/data_files/en-es_trial.json", "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
