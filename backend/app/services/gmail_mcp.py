import asyncio 
import aiohttp
import websockets
import json
import os
import jwt
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

load_dotenv()

# Global variable to store the extracted endpoint
extracted_endpoint = None

def get_possible_endpoints():
    """Get list of possible MCP endpoints including extracted endpoint"""
    endpoints = []
    
    if extracted_endpoint:
        endpoints.append(extracted_endpoint)
        print(f"Added extracted endpoint: {extracted_endpoint}")
    
    return endpoints

async def make_mcp_request(endpoint, payload, description="MCP request"):
    """Make a JSON-RPC request to an MCP endpoint"""
    user_token = create_user_token()
    
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"Trying endpoint: {endpoint}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                endpoint, 
                headers=headers, 
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                print(f"Status: {response.status}")
                response_text = await response.text()
                
                if response.status in [200, 202]:
                    try:
                        response_json = json.loads(response_text)
                        print(f"SUCCESS! {description} response (Status {response.status}):")
                        print(json.dumps(response_json, indent=2))
                        return response_json
                    except json.JSONDecodeError:
                        print(f"Response not JSON (Status {response.status}): {response_text}")
                        if response.status == 202:
                            print("Status 202 likely means no integrations are configured yet")
                        return {"status": response.status, "text": response_text}
                else:
                    print(f"Error {response.status}: {response_text}")
                    return None
                    
    except asyncio.TimeoutError:
        print(f"Timeout for {endpoint}")
        return None
    except aiohttp.ClientError as e:
        print(f"Connection error for {endpoint}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error for {endpoint}: {e}")
        return None

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
        'sub': "user_123",  # Required subject claim for Paragon
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

async def list_mcp_tools():
    """
    Send a POST request to list available MCP tools
    Uses JSON-RPC format which is the standard for MCP
    """
    request_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    possible_endpoints = get_possible_endpoints()
    
    for endpoint in possible_endpoints:
        result = await make_mcp_request(endpoint, request_payload, "Tools list")
        if result:
            return result
    
    print("Could not find working endpoint for tools/list")
    return None

async def test_mcp_tool_call(tool_name, params=None):
    """
    Test calling a specific MCP tool
    """
    request_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": params or {}
        }
    }
    
    # Try different possible endpoints
    possible_endpoints = [
        "http://localhost:3001/",           # Root endpoint
        "http://localhost:3001/mcp",        # MCP specific endpoint  
        "http://localhost:3001/rpc",        # RPC endpoint
        "http://localhost:3001/api",        # API endpoint
        "http://localhost:3001/messages",   # Messages endpoint (session-based)
        "http://localhost:3001/tools/list", # Direct tools endpoint
        "http://localhost:3001/tools"       # Tools base endpoint
    ]
    
    for endpoint in possible_endpoints:
        print(f"Testing tool '{tool_name}' at endpoint: {endpoint}")
        result = await make_mcp_request(endpoint, request_payload, f"Tool call '{tool_name}'")
        if result:
            return result
    
    print(f"Could not call tool '{tool_name}' at any endpoint")
    return None

async def test_connection():
    global extracted_endpoint
    
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
                            
                            # Extract endpoint ID from SSE data
                            if decoded_line.startswith("data: /"):
                                endpoint_path = decoded_line.replace("data: ", "")
                                if endpoint_path.startswith("/messages"):
                                    full_endpoint = f"http://localhost:3001{endpoint_path}"
                                    extracted_endpoint = full_endpoint
                                    print(f"Extracted endpoint: {extracted_endpoint}")

                                    await list_mcp_tools()
                                    
                        elif decoded_line == "":  # Empty line indicates end of event
                            print("Event boundary")
                    except UnicodeDecodeError as e:
                        print(f"Decode error: {e}")
                        continue

        print("Connection closed")
        if extracted_endpoint:
            print(f"Successfully extracted endpoint: {extracted_endpoint}")
        else:
            print("No endpoint extracted from SSE connection")

    except aiohttp.ClientError as e:
        print(f"Client error: {e}")
    except Exception as e:
        print(f"Connection error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """
    Main function to test different MCP operations
    """
    print("Starting MCP Client Tests")
    print("=" * 50)

    # Test 1: Test SSE Connection
    print("\nTest 1: Testing SSE Connection")
    print("-" * 30)
    try:
        await test_connection()
    except Exception as e:
        print(f"SSE connection failed: {e}")
    
    print("\nAll tests completed!")
    
    # Test 2: List MCP Tools
    print("\nTest 2: Listing MCP Tools")
    print("-" * 30)
    tools_result = await list_mcp_tools()
    
    if tools_result:
        print("Tools listing successful!")
        
        # Test 3: Try calling a specific tool if available
        print("\nTest 3: Testing Tool Call")
        print("-" * 30)
        
        # You can modify this to test a specific tool from your list
        # For example, if you have a "gmail.send_email" tool:
        # await test_mcp_tool_call("gmail.send_email", {"to": "test@example.com", "subject": "Test"})
        
        # For now, let's try a generic test
        await test_mcp_tool_call("test_tool", {"test": "value"})
    else:
        print("Tools listing failed")
    


if __name__ == "__main__":
    asyncio.run(test_connection())


