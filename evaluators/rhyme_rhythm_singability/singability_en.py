# Analyse rhyme patterns, syllable line counts, and stress patterns
import pronouncing
import textstat
import time
import re
from syltippy import syllabize


# Get syllable count for sentence
def syllabize_sentence(sentence, language):
    words = sentence.split()
    if language == "en":
        return sum(count_syllables_english(word) or count_syllables_english_fallback(word) for word in words)
    elif language == "es":
        return sum(count_syllables_spanish(word) for word in words)
    #else:
        # Irish


# Counting syllables of inputed English word
def count_syllables_english(word):
    phones = pronouncing.phones_for_word(word)
    if phones:
        return pronouncing.syllable_count(phones[0])
    return None  # Word not found in CMU dictionary


# Fallback function using textstat to count word syllables if pronouncing fails
def count_syllables_english_fallback(word):
    count = textstat.syllable_count(word)  # Fallback method
    if count is None:
        return 0
    return count


#  Counting syllables of inputed Spanish word
def count_syllables_spanish(word):
    # Using syltippy for Spanish phonetic transcription
    syllables, stress = syllabize(word)
    return len(syllables)    



# Test the function
sentence = "We are family, benevolent feelings will last"
syllable_count = syllabize_sentence(sentence, "en")
print(f"Number of syllables in '{sentence}': {syllable_count}")



