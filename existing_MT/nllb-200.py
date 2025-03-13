import json
import threading
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from tqdm import tqdm  # Progress bar library
import torch  # For GPU handling

MODEL_NAME = "facebook/nllb-200-distilled-600M"
LANG_ID = "spa_Latn"  # Spanish language token

# Device setup (use GPU if available)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def load_model_and_tokenizer():
    """Load the model and tokenizer inside each thread to avoid sharing state."""
    TOKENIZER = AutoTokenizer.from_pretrained(MODEL_NAME)
    MODEL = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)
    return TOKENIZER, MODEL

def translate_texts(texts, TOKENIZER, MODEL):
    """Function to translate a list of texts."""
    # Tokenize the input batch
    inputs = TOKENIZER(texts, return_tensors="pt", padding=True, truncation=True).to(device)

    # Use torch.no_grad() to avoid unnecessary gradient computation during inference
    with torch.no_grad():
        # Generate translations
        outputs = MODEL.generate(**inputs, max_length=512, forced_bos_token_id=TOKENIZER.convert_tokens_to_ids(LANG_ID))
    
    # Decode translations
    translated_batch = TOKENIZER.batch_decode(outputs, skip_special_tokens=True)
    return translated_batch

def process_batch(batch, results, idx):
    """Worker function to process a batch of text in a separate thread."""
    # Load model and tokenizer in each thread to avoid resource conflicts
    TOKENIZER, MODEL = load_model_and_tokenizer()
    translated_batch = translate_texts(batch, TOKENIZER, MODEL)
    results[idx] = translated_batch

def main():
    input_file = "/Users/danielhughes/Documents/College/Fourth-Year/Capstone/Dissertation/es_txt_files/originals.txt"
    output_file = "/Users/danielhughes/Documents/College/Fourth-Year/Capstone/Dissertation/es_txt_files/nllbs.txt"

    # Load the file
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    BATCH_SIZE = 25  # Adjust batch size based on memory availability

    print(f"Total lines to translate: {len(lines)}")

    # Split lines into batches
    batches = [lines[i:i + BATCH_SIZE] for i in range(0, len(lines), BATCH_SIZE)]

    # Create a list to store results from each thread
    results = [None] * len(batches)

    # List to hold threads
    threads = []

    # Use threading for parallel processing
    for i, batch in enumerate(batches):
        thread = threading.Thread(target=process_batch, args=(batch, results, i))
        threads.append(thread)
        thread.start()

    # Use tqdm for the progress bar
    for i, thread in enumerate(threads):
        thread.join()  # Wait for all threads to finish
        tqdm.write(f"Batch {i+1}/{len(batches)} completed")

    # Flatten the list of lists into a single list
    translated_lines = [line for batch in results for line in batch]

    # Write translations to output file
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("\n".join(translated_lines))

    print("Parallel translation complete!")

if __name__ == "__main__":
    main()
