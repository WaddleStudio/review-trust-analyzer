import nltk
from nltk.corpus import wordnet

# Download WordNet data
try:
    nltk.data.find('corpora/wordnet.zip')
except LookupError:
    print("Downloading WordNet...")
    nltk.download('wordnet')

BASE_KEYWORDS = ["gift", "discount", "promo", "free", "offer", "coupon", "voucher", "deal", "sale"]

def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            # Replace underscore with space, and keep only single words or short phrases
            syn_word = lemma.name().replace('_', ' ').lower()
            synonyms.add(syn_word)
    return synonyms

def expand_keywords():
    expanded_set = set(BASE_KEYWORDS)
    print(f"Base keywords: {BASE_KEYWORDS}")
    
    for keyword in BASE_KEYWORDS:
        syns = get_synonyms(keyword)
        # Filter out very long phrases or irrelevant words if needed
        # For now, let's keep it simple
        new_words = syns - expanded_set
        if new_words:
            print(f"Found synonyms for '{keyword}': {', '.join(list(new_words)[:5])}...")
        expanded_set.update(syns)
        
    # Sort and print list for copy-pasting
    final_list = sorted(list(expanded_set))
    print("\n--- Expanded Keyword List ---")
    print("[\n    " + ",\n    ".join(f'"{w}"' for w in final_list) + "\n]")

if __name__ == "__main__":
    expand_keywords()
