import json
import multiprocessing
from google.cloud import translate_v2 as translate


def translate_texts(target: str, texts: list) -> list:
    """Translates a batch of texts into the target language using Google Translate API."""
    
    translate_client = translate.Client()

    # Clean input texts (remove newlines, ensure they're strings)
    texts = [t.strip() for t in texts if t.strip()]

    # Ensure all text inputs are strings
    texts = [t.decode("utf-8") if isinstance(t, bytes) else t for t in texts]

    # Call API in batch mode
    results = translate_client.translate(texts, target_language=target)

    # Extract and return translations
    return [result["translatedText"] for result in results]


def process_batch(batch):
    """Worker function to process a batch of text."""
    return translate_texts("es", batch)


def main():
    input_file = "/Users/danielhughes/Documents/College/Fourth-Year/Capstone/Dissertation/es_txt_files/originals.txt"
    output_file = "/Users/danielhughes/Documents/College/Fourth-Year/Capstone/Dissertation/es_txt_files/googles.txt"

    # Load input lines
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"Total lines to translate: {len(lines)}")

    batch_size = 50  # Adjust batch size
    batches = [lines[i:i + batch_size] for i in range(0, len(lines), batch_size)]

    # Use multiprocessing to process batches in parallel
    num_workers = min(multiprocessing.cpu_count(), len(batches))  # Limit workers to available batches
    with multiprocessing.Pool(processes=num_workers) as pool:
        translated_batches = pool.map(process_batch, batches)  # Distribute work

    # Flatten the list of lists
    translated_lines = [line for batch in translated_batches for line in batch]

    # Write translations to output file
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("\n".join(translated_lines))

    print("Parallel translation complete!")

if __name__ == "__main__":
    main()
