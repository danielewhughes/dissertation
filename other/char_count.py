import json

with open("/Users/danielhughes/Documents/College/Fourth-Year/Capstone/Dissertation/data_files/en-ga.json", "r", encoding="utf-8") as f:
        songs = json.load(f)

new_songs = []
for song in songs:
    if song["original-lyrics"].count("\n") != song["translated-lyrics"].count("\n"):
        song_object = {
            "title": song["title"],
            "original-lyrics-count": song["original-lyrics"].count("\n"),
            "translated-lyrics-count": song["translated-lyrics"].count("\n"),
        }
        new_songs.append(song_object)


# Save all songs to a JSON file
with open("check2.json", "w", encoding="utf-8") as file:
    json.dump(new_songs, file, indent=4, ensure_ascii=False)
