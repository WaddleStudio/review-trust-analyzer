import requests
import csv
import io

def test_batch_upload():
    url = "http://localhost:8000/reviews/batch"
    file_path = "d:/Projects/review-trust-analyzer/data/sample_reviews.csv"
    
    print(f"Testing batch upload with {file_path}...")
    
    with open(file_path, "rb") as f:
        files = {"file": ("sample_reviews.csv", f, "text/csv")}
        response = requests.post(url, files=files)
        
    if response.status_code == 200:
        results = response.json()
        print(f"Success! Analyzed {len(results)} reviews.")
        
        print("\n--- Sample Results ---")
        for i, res in enumerate(results[:5]):
            print(f"Review {i+1}: Score={res['trust_score']:.2f}, Suspicious={res['is_suspicious']}, Reasons={res['reasons']}")
            
        # Verify specific cases
        # Case 2 in CSV is "Show this review to get a free dessert." -> Should be suspicious
        if results[1]['is_suspicious']:
            print("\n[PASS] Promo review detected correctly.")
        else:
            print("\n[FAIL] Promo review NOT detected.")
            
        # Case 6 is "讚" -> Should be safe (short text)
        if not results[5]['is_suspicious']:
             print("[PASS] Short text '讚' marked as safe.")
        else:
             print("[FAIL] Short text '讚' marked as suspicious.")

    else:
        print(f"Failed. Status Code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_batch_upload()
