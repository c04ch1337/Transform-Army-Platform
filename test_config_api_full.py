import requests
import json

BASE_URL = "http://localhost:8000"
AGENT_ID = "agent_bdr_concierge"

print("Testing Full Agent Configuration API")
print("="*60)

# Test 1: GET - Read current config
print("\n[TEST 1] GET /api/v1/agents/{agent_id}/config")
response = requests.get(f"{BASE_URL}/api/v1/agents/{AGENT_ID}/config")
print(f"Status: {response.status_code}")
original_config = response.json()
print(f"Agent: {original_config['config']['name']}")
print(f"Version: {original_config['metadata']['version']}")
print(f"Temperature: {original_config['config']['model']['temperature']}")

# Test 2: PUT - Update config
print("\n[TEST 2] PUT /api/v1/agents/{agent_id}/config")
updated_config = original_config['config'].copy()
updated_config['model']['temperature'] = 0.5  # Change temperature
response = requests.put(f"{BASE_URL}/api/v1/agents/{AGENT_ID}/config", json=updated_config)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"New Version: {data['metadata']['version']}")
    print(f"New Temperature: {data['config']['model']['temperature']}")

# Test 3: History - Check versions
print("\n[TEST 3] GET /api/v1/agents/{agent_id}/config/history")
response = requests.get(f"{BASE_URL}/api/v1/agents/{AGENT_ID}/config/history")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Total versions: {data['total_versions']}")
    for v in data['history']:
        print(f"  - Version {v['version']}: {v['changes']}")

# Test 4: Validate invalid config
print("\n[TEST 4] POST /api/v1/agents/{agent_id}/config/validate (invalid)")
invalid_config = {
    "name": "Test",
    "model": {"temperature": 5.0}  # Invalid temperature
}
response = requests.post(f"{BASE_URL}/api/v1/agents/{AGENT_ID}/config/validate", json=invalid_config)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Valid: {data['is_valid']}")
    if not data['is_valid']:
        print(f"Errors: {data['errors']}")

# Test 5: Restore previous version
print("\n[TEST 5] POST /api/v1/agents/{agent_id}/config/restore")
restore_data = {"version": 1}
response = requests.post(f"{BASE_URL}/api/v1/agents/{AGENT_ID}/config/restore", json=restore_data)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Restored to version: {data['metadata']['restored_from_version']}")
    print(f"New version: {data['metadata']['version']}")
    print(f"Temperature restored to: {data['config']['model']['temperature']}")

# Test 6: Reset to default
print("\n[TEST 6] POST /api/v1/agents/{agent_id}/config/reset")
response = requests.post(f"{BASE_URL}/api/v1/agents/{AGENT_ID}/config/reset")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Reset successful! Version: {data['metadata']['version']}")
    print(f"Is default: {data['metadata']['is_default']}")

# Final check - Get all history
print("\n[FINAL] Check complete history")
response = requests.get(f"{BASE_URL}/api/v1/agents/{AGENT_ID}/config/history")
if response.status_code == 200:
    data = response.json()
    print(f"Total versions now: {data['total_versions']}")
    for v in data['history'][:5]:  # Show last 5
        print(f"  - Version {v['version']}: {v['changes']}")

print("\n" + "="*60)
print("SUCCESS: All tests complete!")