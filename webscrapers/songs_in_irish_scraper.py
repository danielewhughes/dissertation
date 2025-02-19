import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Initialize Selenium WebDriver (e.g., Chrome)
driver = webdriver.Chrome()  # Adjust if using a different browser driver
driver.maximize_window()

# Base URL
URL = "https://songsinirish.com/a-z/"

# Navigate to the main page
driver.get(URL)

# Wait for the required content to load
try:
    div = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "col-3"))
    )
    # Extract text and href immediately to avoid stale elements
    links = [
        {
            "name": link.find_element(By.TAG_NAME, "a").text.strip(),
            "url": link.find_element(By.TAG_NAME, "a").get_attribute("href"),
        }
        for link in div.find_elements(By.TAG_NAME, "li")
    ]
except Exception as e:
    print(f"Error finding links: {e}")
    driver.quit()
    exit()

song_list = []
count = 0

# Process each link
for link in links:
    song_name = link["name"]
    song_link = link["url"]
    try:
        # Navigate to the song page
        driver.get(song_link)

        # Skip if the page contains a "Machine Translation" warning
        if driver.find_elements(By.CLASS_NAME, "gt-warning"):
            print("Machine translation found, skipping...")
            continue

        # Prepare the song object
        song_object = {
            "title": song_name,
            "original-lyrics": "",
            "translated-lyrics": "",
            "google-translation": "",
            "microsoft-translation": "",
            "nllb-200-translation": "",
            "deepl-translation": "",
        }

        # Extract English lyrics
        try:
            # Wait for the English lyrics div to load
            english_div = WebDriverWait(driver, 30).until(
                # Using multiple selectors here as div for English lyrics can vary
                EC.presence_of_element_located((By.CSS_SELECTOR, "#en.pure-u-1.pure-u-md-1-2, #en.pure-u-1.pure-u-md-1-2.lyrics-overflow"))
            )

            # Extract the text from each <p> tag using `textContent`
            paragraphs = english_div.find_elements(By.TAG_NAME, "p")
            if not paragraphs:
                print("No <p> tags found in the English lyrics div.")
                continue  # Skip to the next loop iteration
            
            # Combine the text from the <p> tags
            english_lyrics = "\n\n".join(
                p.get_attribute("textContent").strip() for p in paragraphs if p.get_attribute("textContent").strip()
                    
            )
            english_lyrics = english_lyrics.replace(" (after each verse)", "")
            if "\n-\n" in english_lyrics or not english_lyrics:
                print("No text content found in the English lyrics.")
                continue
            
            song_object["original-lyrics"] = english_lyrics
        except Exception as e:
            print(f"Error extracting English lyrics: {e}")
            continue  # Skip to the next loop iteration



        # Extract Irish lyrics (dynamically rendered)
        try:
            irish_div = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "teacs-gaeilge"))
            )
            paragraphs = irish_div.find_elements(By.TAG_NAME, "p")
            irish_lyrics = "\n\n".join(p.text for p in paragraphs)
            irish_lyrics = irish_lyrics.replace(" (i ndiaidh gach véarsa)", "")
            if "we haven't transcribed the lyrics for this yet" in irish_lyrics:
                print("Lyrics not transcribed yet.")
                continue
            song_object["translated-lyrics"] = irish_lyrics
        except Exception:
            print("Irish lyrics not found.")

        # Add song object to the list
        song_list.append(song_object)
        count += 1
        print(f"Processed song {count}: {song_name}")
    except Exception as e:
        print(f"Error processing {song_link}: {e}")
        continue

# Close the Selenium browser
driver.quit()

# Save all songs to a JSON file
with open("en-ga-2.json", "w", encoding="utf-8") as file:
    json.dump(song_list, file, indent=4, ensure_ascii=False)
print(f"Saved {len(song_list)} songs to en-ga-trial.json.")
