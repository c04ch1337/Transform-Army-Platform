import requests
import json

BASE_URL = "http://localhost:8000"

print("Testing Agent Configuration API\n" + "="*50)

# Test 1: GET config
print("\n1. Testing GET /api/v1/agents/agent_bdr_concierge/config")
response = requests.get(f"{BASE_URL}/api/v1/agents/agent_bdr_concierge/config")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Agent: {data['config']['name']}")
    print(f"Version: {data['metadata']['version']}")
    print(f"Functions: {len(data['config']['functions'])}")
else:
    print(f"Error: {response.text}")

# Test 2: History
print("\n2. Testing GET /api/v1/agents/agent_bdr_concierge/config/history")
response = requests.get(f"{BASE_URL}/api/v1/agents/agent_bdr_concierge/config/history")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Total versions: {data['total_versions']}")
    print(f"Returned: {data['returned']}")

# Test 3: Validate
print("\n3. Testing POST /api/v1/agents/agent_bdr_concierge/config/validate")
test_config = {
    "name": "Test Agent",
    "model": {"model": "gpt-4", "temperature": 0.7, "maxTokens": 500},
    "voice": {"provider": "11labs", "voiceId": "test123"},
    "serverUrl": "https://test.com",
    "functions": []
}
response = requests.post(f"{BASE_URL}/api/v1/agents/agent_bdr_concierge/config/validate", json=test_config)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Valid: {data['is_valid']}")
    print(f"Errors: {data['errors']}")

print("\n" + "="*50)
print("Tests complete!")