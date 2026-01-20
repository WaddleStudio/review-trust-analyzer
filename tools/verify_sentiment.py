import pytest
from features.text_features import extract_text_features

def test_sentiment_comparison():
    # Case 1: Positive but simple (Old method might score this similarly to complex one, but let's see)
    text_simple_good = "good product"
    
    # Case 2: Complex positive (TextBlob should handle this better)
    text_complex_good = "I absolutely adored this wonderful masterpiece of a hotel."
    
    # Case 3: Mixed/Sarcastic (TextBlob might struggle with sarcasm but handles mixed better than keyword count)
    text_mixed = "The food was good but the service was terrible."
    
    features_1 = extract_text_features(text_simple_good)
    features_2 = extract_text_features(text_complex_good)
    features_3 = extract_text_features(text_mixed)
    
    print(f"\n--- Sentiment Analysis Verification ---")
    print(f"Text: '{text_simple_good}' -> Score: {features_1['sentiment_score']:.4f}")
    print(f"Text: '{text_complex_good}' -> Score: {features_2['sentiment_score']:.4f}")
    print(f"Text: '{text_mixed}' -> Score: {features_3['sentiment_score']:.4f}")
    
    # Assertions to verify expected behavior
    assert features_2['sentiment_score'] > 0.5, "Complex positive should have high score"
    assert features_3['sentiment_score'] < features_1['sentiment_score'], "Mixed review should be lower than pure positive"

if __name__ == "__main__":
    test_sentiment_comparison()
