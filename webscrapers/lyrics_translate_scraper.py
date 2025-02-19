import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException

# Initialize Selenium WebDriver (e.g., Chrome)
driver = webdriver.Chrome()  # Adjust if using a different browser driver
driver.maximize_window()

# Base URL
URL = "https://lyricstranslate.com/en/translations/328/42/none/none/none/0/0/0/1037138?order=Relevance"

# Navigate to the main page
driver.get(URL)
links = []

while True:
    # Wait for the required content to load
    try:
        div = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "t-s-r"))
        )
        # Extract text and href immediately to avoid stale elements
        links.extend(
            [
                {
                    "name": link.find_element(By.TAG_NAME, "a").text.strip(),
                    "url": link.find_element(By.TAG_NAME, "a").get_attribute("href"),
                }
                for link in div.find_elements(By.CLASS_NAME, "stt")
            ]
        )
    except Exception as e:
        print(f"Error finding links: {e}")
        driver.quit()
        exit()

    try:
        next_page_div = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pager-next"))
        )
        next_page_link = next_page_div.find_element(By.TAG_NAME, "a")
        if next_page_link:
            next_page_link.click()  # Click the next page link
            WebDriverWait(driver, 30).until(
                EC.staleness_of(next_page_div)  # Wait for the page to load before continuing
            )
    except:
        break

song_list = []
count = 0

# Process each link
for link in links:
    song_name = link["name"]
    song_link = link["url"]
    try:
        # Navigate to the song page
        driver.get(song_link)

        # Prepare the song object
        song_object = {
            "title": song_name,
        }

        # Locate the dotted_link element if it exists
        try:
            dotted_link = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//a[@class='dottedlink' and contains(text(), 'original lyrics')]"))
            )
            # Retrieve the text of the dotted_link element
            dotted_link_text = dotted_link.text.strip()
            if dotted_link_text == "Click to see the original lyrics (English)":
                # Navigate to original lyrics page
                driver.execute_script("arguments[0].scrollIntoView(true);", dotted_link)
                time.sleep(2)  # Allow time for scrolling animation if necessary
                driver.execute_script("arguments[0].click();", dotted_link)
                time.sleep(5) #Allow for page to load
            else:
                # Dotted_link text contains "(English, X)" where X is another language
                print(f"Found multilingual original lyrics link: '{dotted_link_text}'. Skipping this song.")
                continue  # Skip to the next iteration of the for loop
        except:
            # The dotted_link element does not exist
            pass  # Proceed without clicking

        # Extract English lyrics
        try:
            english_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "song-body"))
            )
            english_lyrics = [
                par.get_attribute("textContent").strip() + "\n"
                for par in english_div.find_elements(By.CLASS_NAME, "par")
            ]
            print(english_lyrics)
            song_object["original-lyrics"] = "\n".join(english_lyrics)
        except Exception as e:
            print(f"Error extracting English lyrics: {e}")
            continue  # Skip if English lyrics aren't available
        
        # Extract Spanish lyrics only if English lyrics are present
        try:
            spanish_div = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "translation-body"))
            )
            spanish_lyrics = [
                paragraph.get_attribute("textContent").strip() + "\n"
                for paragraph in spanish_div.find_elements(By.CLASS_NAME, "par")
            ]
            print(spanish_lyrics)
            song_object["translated-lyrics"] = "\n".join(spanish_lyrics)
        except Exception as e:
            print(f"Error extracting Spanish lyrics: {e}")
            continue  # Skip if Spanish lyrics aren't available

        if "original-lyrics" in song_object and "translated-lyrics" in song_object:
            song_list.append(song_object)
            count += 1
            print(f"Processed song {count}: {song_name}")
        else:
            print(f"Skipping song due to incomplete data: {song_name}")
    except Exception as e:
        print(f"Error processing {song_link}: {e}")
        continue

# Close the Selenium browser
driver.quit()

# Save all songs to a JSON file
with open("en_es_2.json", "w", encoding="utf-8") as file:
    json.dump(song_list, file, indent=4, ensure_ascii=False)
print(f"Saved {len(song_list)} songs to en_es.json.")
