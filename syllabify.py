VOWELS = "aeiouy"
DIPHTHONGS = ["ae", "au", "ei", "eu", "oe"]
MUTE_LIQUIDS = ["pl", "pr", "bl", "br", "cl", "cr", "gl", "gr", "tl", "tr", "dr"]
CONSONANT_CLUSTERS = ["qu", "gu", "su", "ch", "ph", "th"]
APPROXIMANT_CLUSTERS = ["qu", "gu"]
SU_CLUSTERS = ["suav", "suesc", "suad", "suet"]
UI_DIPHTHONG = ["cui", "hui"]

def is_consonant_i(word, i):
    # assert word[i] == i, "passed in a non-i into is_consonant_i"
    if word[i] != "i": return False
    
    # Intervocalic or word initial i + vowel
    if (i + 1) >= len(word) or word[i+1] not in VOWELS:
        return False

    #   word-initial    intervocalic
    return i == 0 or word[i-1] in VOWELS

def is_su_cluster(word, i):
    if word[i:i+2] != "su":
        return False

    return any(word[i:i+len(cluster)] == cluster for cluster in SU_CLUSTERS)

def is_ui_diphthong(word, i):
    if word[i:i+2] != "ui":
        return False

    return any(word[i-(len(ui)-2):i+2] == ui for ui in UI_DIPHTHONG)

def is_vowel(word, i):
    if is_consonant_i(word, i):
        return False
    if i > 0 and word[i-1:i+1] in APPROXIMANT_CLUSTERS:
        if (i + 1) >= len(word) or word[i+1] != "u": # special-casing stuff like exiguus
            return False
    if i > 0 and is_su_cluster(word, i-1):
        return False
    return word[i] in VOWELS

def syllable_break(cluster):
    if cluster in CONSONANT_CLUSTERS:
        return 0
    if len(cluster) <= 1:
        return 0
    if cluster in MUTE_LIQUIDS:
        return 0
    return 1

def syllabify(word):
    word = word.lower()
    syllables = []
    current = ""
    i = 0

    while i < len(word):
        current += word[i]
        if is_vowel(word, i):
            j = i + 1

            # collapse dipthongs into a single syllable
            if (i + 1) < len(word) and (word[i:i+2] in DIPHTHONGS or is_ui_diphthong(word, i)):
                current += word[i+1]
                j += 1

            saved_j = j
            while j < len(word) and not is_vowel(word, j):
                j += 1
            cluster = word[saved_j:j]

            if j < len(word):
                split = syllable_break(cluster)
                if split == 0:
                    syllables.append(current)
                    current = cluster
                else:
                    syllables.append(current + cluster[:split])
                    current = cluster[split:]
                i = j
            else:
                i = saved_j
        else:
            i += 1
    if current:
        syllables.append(current)
    return syllables

def syllabify_line(line):
    syllables = []
    for word in line.split():
        word = "".join(ch for ch in word if ch.isalpha()) # no punctuation, etc.
        if word: syllables.extend(syllabify(word))
    return syllables

def syllabify_line_indexed(line):
    syllables = []
    syllable_to_word = []
    syllable_in_word = []
    words = []
    for word in line.split():
        words.append(word)
        word = "".join(ch for ch in word if ch.isalpha()) # no punctuation, etc.
        if word: 
            new_syllables = syllabify(word)
            syllables.extend(new_syllables)

            # These are indexed by syllable POSITION
            syllable_to_word.extend([word for i in range(len(new_syllables))])
            # What index each syllable is in the requisite word
            syllable_in_word.extend([i for i in range(len(new_syllables))])
    return syllables

    return words, syllables

#def tokenize_sentence(sentence):
#    words = sentence.lower().split()
#    return [syllabify(word) for word in words]
#
#sentence = input("Enter sentence: ")
#print(tokenize_sentence(sentence))
