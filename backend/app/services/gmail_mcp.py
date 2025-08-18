import asyncio 
import aiohttp
import websockets
import json
import os
import jwt
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

load_dotenv()

print("Hello, world!")

def format_private_key(key_string):
    """
    Format a private key string to proper PEM format for RS256 signing
    """
    if not key_string:
        raise ValueError("Private key is empty")
    
    # Remove any whitespace and newlines
    key_string = key_string.strip()
    
    # Handle literal \n characters in the key string
    if '\\n' in key_string:
        key_string = key_string.replace('\\n', '\n')
    
    # If already in PEM format, return as is
    if key_string.startswith('-----BEGIN'):
        return key_string
    
    # If it's base64 encoded, try to decode it
    import base64
    try:
        decoded_key = base64.b64decode(key_string).decode('utf-8')
        if decoded_key.startswith('-----BEGIN'):
            return decoded_key
    except:
        pass
    
    # If it's a raw key, wrap it in PEM format
    # For RS256, we typically use RSA private keys
    if '-----BEGIN RSA PRIVATE KEY-----' in key_string:
        return key_string
    elif '-----BEGIN PRIVATE KEY-----' in key_string:
        return key_string
    else:
        # Assume it's a raw RSA private key and wrap it
        return f"-----BEGIN PRIVATE KEY-----\n{key_string}\n-----END PRIVATE KEY-----"

def create_user_token():
    # paragon credentials
    signing_key = os.getenv("PARAGON_SIGNING_KEY")
    print(f"Signing key length: {len(signing_key) if signing_key else 0}")
    project_id = os.getenv("PARAGON_PROJECT_ID")
    print(f"Project ID: {project_id}")
    if not signing_key or not project_id:
        raise ValueError("PARAGON_SIGNING_KEY or PARAGON_PROJECT_ID is not set")
    
    # Format the private key properly
    try:
        formatted_key = format_private_key(signing_key)
        print("Private key formatted successfully")
    except Exception as e:
        print(f"Error formatting private key: {e}")
        raise
    
    # create a JWT payload
    payload = {
        'user_id': "user_123",
        "project_id": project_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),  # issued at
        "iss": project_id  # issuer (usually your project ID)
    }

    try:
        # create a JWT token with RS256 algorithm
        token = jwt.encode(payload, formatted_key, algorithm="RS256")
        print("JWT token created successfully")
        return token
    except jwt.InvalidKeyError as e:
        print(f"Invalid key format: {e}")
        raise
    except Exception as e:
        print(f"JWT encoding error: {e}")
        raise

async def test_connection():

    user_token = create_user_token()
    print(f"User token (first 50 chars): {user_token[:50]}...")
    
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Accept": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
    }

    try:
        async with aiohttp.ClientSession() as session:
            print("Connecting to sse...")
            async with session.get("http://localhost:3001/sse?user=user_123", headers=headers) as response:
                print(f"Response status: {response.status}")
                print(f"Response headers: {dict(response.headers)}")
                
                if response.status != 200:
                    print(f"Error: Server returned status {response.status}")
                    error_text = await response.text()
                    print(f"Error response: {error_text}")
                    return
                
                print("Connected to sse successfully")
                
                # Read SSE data properly
                async for line in response.content:
                    try:
                        decoded_line = line.decode("utf-8").strip()
                        if decoded_line:
                            print(f"Received: {decoded_line}")
                        elif decoded_line == "":  # Empty line indicates end of event
                            print("Event boundary")
                    except UnicodeDecodeError as e:
                        print(f"Decode error: {e}")
                        continue

        print("Connection closed")

    except aiohttp.ClientError as e:
        print(f"Client error: {e}")
    except Exception as e:
        print(f"Connection error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_connection())