import json
import re




if __name__ == '__main__':
    with open("/Users/danielhughes/Documents/College/Fourth-Year/Capstone/Dissertation/rhyme_files/googles.txt", "r", encoding="utf-8") as f:
        content = f.readlines()

    cleaned_text = ''.join([line for line in content if line.strip()])

    with open('ga_txt_files/googles.txt', 'w', encoding='utf-8') as file:
        file.write(cleaned_text)


