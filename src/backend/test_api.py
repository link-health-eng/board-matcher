import requests
import sys

API_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint."""
    response = requests.get(f"{API_URL}/health")
    print("Health Check:", response.json())
    return response.json()

def test_upload(file_path):
    """Test uploading a dataset."""
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(f"{API_URL}/upload", files=files)
    
    if response.status_code == 200:
        print("Upload successful:", response.json())
    else:
        print("Upload failed:", response.status_code, response.text)
    
    return response.json()

def test_match(query, top_k=5):
    """Test matching connections."""
    payload = {
        "query": query,
        "top_k": top_k
    }
    response = requests.post(f"{API_URL}/match", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nMatches for: '{query}'")
        print(f"Total matches: {data['total_matches']}\n")
        
        for match in data['matches']:
            print(f"Rank {match['rank']}: {match['name']} (Score: {match['score']:.4f})")
            print(f"  Employment: {match['employment'][:100]}...")
            print(f"  Board Service: {match['board_service'][:100]}...")
            print()
    else:
        print("Match failed:", response.status_code, response.text)
    
    return response.json() if response.status_code == 200 else None

if __name__ == "__main__":
    # Check health
    print("=== Testing Health ===")
    test_health()
    print()
    
    # Upload dataset
    print("=== Testing Upload ===")
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
        test_upload(excel_file)
    else:
        print("Skipping upload - no file provided")
        print("Usage: python test_api.py <path_to_excel_file>")
    print()
    
    # Test matching
    print("=== Testing Match ===")
    test_query = "Boston Red Sox Foundation"
    test_match(test_query, top_k=5)