import json
import deepl
import time
import multiprocessing

# Your DeepL API key
DEEPL_API_KEY = "70fa71af-e618-48f5-ac43-05ee1e79016b:fx"
translator = deepl.Translator(DEEPL_API_KEY)    

def translate_texts(target: str, texts: list) -> list:
    # Clean input texts (remove newlines, ensure they're strings)
    texts = [t.strip() for t in texts if t.strip()]

    # Ensure all text inputs are strings
    texts = [t.decode("utf-8") if isinstance(t, bytes) else t for t in texts]

    # Call API in batch mode
    return translator.translate_text(texts, target_lang="ES")


def process_batch(batch):
    """Worker function to process a batch of text with retry on failure."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return translate_texts("es", batch)  # Translate batch
        except deepl.exceptions.TooManyRequestsException:
            wait_time = (2 ** attempt)  # Exponential backoff (2s, 4s, 8s)
            print(f"Rate limit hit. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    return ["ERROR" for _ in batch]  # Return error placeholders if all retries fail


def main():
    input_file = "/Users/danielhughes/Documents/College/Fourth-Year/Capstone/Dissertation/es_txt_files/originals.txt"
    output_file = "/Users/danielhughes/Documents/College/Fourth-Year/Capstone/Dissertation/es_txt_files/deepls.txt"

    # Load input lines
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"Total lines to translate: {len(lines)}")

    batch_size = 25  # Adjust batch size
    batches = [lines[i:i + batch_size] for i in range(0, len(lines), batch_size)]

    # Use multiprocessing to process batches in parallel
    num_workers = min(4, len(batches))  # Instead of using all CPU cores
    with multiprocessing.Pool(processes=num_workers) as pool:
        translated_batches = pool.map(process_batch, batches)  # Distribute work

    # Flatten the list of lists
    translated_lines = [line.text for batch in translated_batches for line in batch]

    # Write translations to output file
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("\n".join(translated_lines))

    print("Parallel translation complete!")

if __name__ == "__main__":
    main()