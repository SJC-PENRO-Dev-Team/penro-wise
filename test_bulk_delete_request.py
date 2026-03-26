"""
Test what the bulk delete endpoint receives
"""
import json

# Simulate what the frontend sends
request_data = {
    "items": [
        {
            "type": "link-group",
            "id": "33",  # This might be the issue - should be int, not string
            "group_name": "Projects"
        }
    ],
    "step": "3",
    "confirmations": {
        "non_empty_confirmed": True
    }
}

print("Frontend sends:")
print(json.dumps(request_data, indent=2))
print()

# Check data types
item = request_data["items"][0]
print(f"item['id'] type: {type(item['id'])}")
print(f"item['id'] value: {item['id']}")
