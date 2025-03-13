import json
import re


if __name__ == '__main__':
    input_file = "data_files/cleaned_songs.json"
    #output_file1 = "es_txt_files/originals.txt"
    #output_file2 = "es_txt_files/references.txt"
    #output_file3 = "es_txt_files/googles.txt"
    output_file4 = "es_txt_files/nllbs.txt"
    #output_file5 = "es_txt_files/deepls.txt"

    with open(input_file, "r", encoding="utf-8") as f:
        songs = json.load(f)

    with open(output_file4, "w", encoding="utf-8") as file:
        for song in songs:
            file.write(song["deepl-translation"] + "\n*\n")

    #with open(output_file, "w", encoding="utf-8") as f1:
    #    for line in lines:
    #        if line == "\n":
    #            f1.write("*\n")
    #        else:
    #            line = re.sub(r"[^\w\s]", "", line).lower()
    #            f1.write(line)

    #with open(input_file, "w", encoding="utf-8") as f1:
        #for song in songs:
            #outfile1.write(song["original-lyrics"]+ "\n*\n")
            #outfile2.write(song["translated-lyrics"]+ "\n*\n")
            #outfile3.write(song["google-translation"]+ "\n*\n")
            #outfile4.write(song["nllb-200-translation"]+ "\n*\n")
            #outfile5.write(song["deepl-translation"]+ "\n*\n")
            
