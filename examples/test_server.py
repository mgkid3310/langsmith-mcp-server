"""
Test script for LangSmith MCP Server using MCP streamable HTTP client.

Make sure to:
1. Install dependencies: pip install mcp langchain-mcp-adapters httpx python-dotenv
2. Start the server first: uvicorn langsmith_mcp_server.server:app --host 0.0.0.0 --port 8000
3. Set your LangSmith API key: export LANGSMITH_API_KEY=lsv2_pt_... or in .env file
4. Optionally set LANGSMITH_WORKSPACE_ID and LANGSMITH_ENDPOINT in .env file

The server accepts these headers:
- LANGSMITH-API-KEY (required)
- LANGSMITH-WORKSPACE-ID (optional)
- LANGSMITH-ENDPOINT (optional)
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
except ImportError:
    print("❌ Error: mcp is not installed")
    print("   Install it with: pip install mcp")
    sys.exit(1)

try:
    from langchain_mcp_adapters.tools import load_mcp_tools
except ImportError:
    print("❌ Error: langchain-mcp-adapters is not installed")
    print("   Install it with: pip install langchain-mcp-adapters")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("❌ Error: httpx is not installed")
    print("   Install it with: pip install httpx")
    sys.exit(1)


async def test_langsmith_mcp_server():
    """Test the LangSmith MCP server locally."""
    
    # Get API key from environment
    api_key = os.getenv("LANGSMITH_API_KEY")
    
    if not api_key:
        print("⚠️  Warning: Please set your LANGSMITH_API_KEY environment variable")
        print("   Example: export LANGSMITH_API_KEY=lsv2_pt_...")
        print("   Or create a .env file with:")
        print("     LANGSMITH_API_KEY=lsv2_pt_...")
        print("     LANGSMITH_WORKSPACE_ID=your_workspace_id (optional)")
        print("     LANGSMITH_ENDPOINT=https://api.smith.langchain.com (optional)")
        return
    
    base_url = "http://localhost:8000"
    mcp_url = f"{base_url}/mcp"
    
    print("🚀 Connecting to LangSmith MCP Server...")
    print(f"   URL: {mcp_url}")
    print(f"   API Key: {api_key[:10]}...")
    print()
    
    # First, check if server is running
    print("📡 Checking if server is running...")
    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(f"{base_url}/health", timeout=5.0)
            if response.status_code == 200:
                print(f"   ✅ Server is running! Health check: {response.text}")
            else:
                print(f"   ⚠️  Server responded with status {response.status_code}")
    except httpx.ConnectError:
        print(f"   ❌ Cannot connect to server at {base_url}")
        print("   Make sure the server is running:")
        print("   uvicorn langsmith_mcp_server.server:app --host 0.0.0.0 --port 8000")
        return
    except Exception as e:
        print(f"   ⚠️  Error checking server: {e}")
    print()
    
    # Create headers with API key and optional config
    headers = {
        "LANGSMITH-API-KEY": api_key,
    }
    
    # Add optional headers if provided
    workspace_id = os.getenv("LANGSMITH_WORKSPACE_ID")
    endpoint = os.getenv("LANGSMITH_ENDPOINT")
    
    if workspace_id:
        headers["LANGSMITH-WORKSPACE-ID"] = workspace_id
        print(f"   Workspace ID: {workspace_id}")
    if endpoint:
        headers["LANGSMITH-ENDPOINT"] = endpoint
        print(f"   Endpoint: {endpoint}")
    print()
    
    try:
        # Connect using streamable HTTP client
        async with streamablehttp_client(mcp_url, headers=headers) as (read, write, _):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                print("📋 Initializing MCP session...")
                await session.initialize()
                print("   ✅ Session initialized")
                print()
                
                # Test 1: Get available tools
                print("📋 Test 1: Getting available tools...")
                tools = await load_mcp_tools(session)
                print(f"   ✅ Found {len(tools)} tools:")
                # tools is a list, not a dict
                for tool in tools:
                    tool_name = getattr(tool, 'name', str(tool))
                    print(f"      - {tool_name}")
                print()
                
                # Test 2: List tools directly from session
                print("📋 Test 2: Listing tools from session...")
                try:
                    tools_result = await session.list_tools()
                    print(f"   ✅ Found {len(tools_result.tools)} tools:")
                    for tool in tools_result.tools:
                        print(f"      - {tool.name}: {tool.description[:60]}...")
                except Exception as e:
                    print(f"   ⚠️  Error listing tools: {e}")
                print()
                
                # Test 3: List prompts
                print("📋 Test 3: Listing prompts...")
                try:
                    prompts_result = await session.list_prompts()
                    print(f"   ✅ Found {len(prompts_result.prompts)} prompts:")
                    for prompt in prompts_result.prompts:
                        print(f"      - {prompt.name}")
                except Exception as e:
                    print(f"   ⚠️  Error listing prompts: {e}")
                print()
                
                # Test 4: List resources
                print("📋 Test 4: Listing resources...")
                try:
                    resources_result = await session.list_resources()
                    print(f"   ✅ Found {len(resources_result.resources)} resources:")
                    for resource in resources_result.resources:
                        print(f"      - {resource.uri}")
                except Exception as e:
                    print(f"   ⚠️  Error listing resources: {e}")
                print()
                
                # Test 5: Call a tool (list_prompts)
                print("📋 Test 5: Calling list_prompts tool...")
                try:
                    result = await session.call_tool(
                        "list_prompts",
                        arguments={"limit": 5, "is_public": "false"}
                    )
                    print(f"   ✅ Success! Tool called")
                    if hasattr(result, 'content'):
                        print(f"   📊 Result has {len(result.content)} content items")
                        if result.content:
                            # Try to extract some info from the result
                            first_item = result.content[0]
                            if hasattr(first_item, 'text'):
                                text = first_item.text[:200]
                                print(f"   📄 First result preview: {text}...")
                    else:
                        print(f"   📊 Result type: {type(result)}")
                except Exception as e:
                    print(f"   ❌ Error calling tool: {e}")
                    import traceback
                    traceback.print_exc()
                print()
                
                print("✅ All tests completed!")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 LangSmith MCP Server Test Script")
    print("=" * 60)
    print()
    print("📝 Prerequisites:")
    print("   1. Start the server: uvicorn langsmith_mcp_server.server:app --host 0.0.0.0 --port 8000")
    print("   2. Set LANGSMITH_API_KEY environment variable")
    print()
    print("-" * 60)
    print()
    
    asyncio.run(test_langsmith_mcp_server())

