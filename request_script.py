import requests
import json
import uuid
from pprint import pprint

def send_chat_request(user_message):
    """
    Sends a request to the chat endpoint and returns the response.
    
    Args:
        user_message (str): The message from the user to send to the chatbot
        
    Returns:
        dict: The JSON response from the server
    """
    # API endpoint URL with correct prefix from routes/__init__.py
    url = "http://localhost:5005/api/v1/chat/message"
    
    # Generate a random UUID for the session
    session_id = str(uuid.UUID('c083285c-2ab7-47ba-a351-738e32a07b54'))
    
    # Prepare headers and payload
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "user_message": user_message,
        "session_identifier": session_id
    }
    
    print(f"Sending request to: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Send POST request
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        # Parse and return JSON response
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending request: {e}")
        return None

if __name__ == "__main__":
    # Example message to send
    message = "Buradan ne anlamalıyım?"
    
    print(f"Sending message: '{message}'")
    response = send_chat_request(message)
    
    if response:
        print("\nResponse received:")
        pprint(response)
    else:
        print("Failed to get response from the server.")
