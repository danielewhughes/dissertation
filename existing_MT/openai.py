import openai
import json
import time

# Set your OpenAI API key
openai.api_key = "YOUR_OPENAI_API_KEY"

# Function to translate a batch of sentences using GPT-3.5 Turbo
def translate_texts(texts, target_language="Spanish"):
    translations = []
    for text in texts:
        # Create a prompt asking the model to translate the sentence
        prompt = f"Translate the following sentence to {target_language}: {text}"

        try:
            # Make the API call to OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Using GPT-3.5 Turbo
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,  # Limit the response tokens if needed
                n=1,  # Number of responses to generate
                stop=None,  # You can define stop sequences here if necessary
            )

            # Extract the translation from the response
            translation = response['choices'][0]['message']['content'].strip()
            translations.append(translation)

            # Optional: Add a small delay to prevent hitting rate limits
            time.sleep(1)

        except Exception as e:
            print(f"Error while translating: {e}")
            translations.append(None)  # Append None if there was an error

    return translations


# Main function to process a file with sentences
def main():
    input_file = "es_txt_files/originals.txt"  # Path to your input file with sentences
    output_file = "es_txt_files/openais.txt"  # Output file for translations

    # Read the sentences from the input file
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"Total sentences to translate: {len(lines)}")

    # Translate the sentences using GPT-3.5 Turbo
    translated_sentences = translate_texts(lines, target_language="Spanish")

    # Write the translations to the output file
    with open(output_file, "w", encoding="utf-8") as f:
        for translation in translated_sentences:
            f.write(f"{translation}\n")

    print(f"Translation complete! Translations saved to {output_file}")


if __name__ == "__main__":
    main()
