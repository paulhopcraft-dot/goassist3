"""Test script for voice pipeline E2E verification.

Tests the complete GoAssist voice pipeline with vLLM backend.
Run after starting GoAssist server with: python -m src.main
"""
import asyncio
import sys

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx


async def test_health(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test health endpoint."""
    print("1. Checking health...")
    try:
        r = await client.get(f"{base_url}/health")
        if r.status_code == 200:
            data = r.json()
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Ready: {data.get('ready', False)}")
            return True
        else:
            print(f"   Failed: HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"   Error: {e}")
        return False


async def test_session_lifecycle(client: httpx.AsyncClient, base_url: str) -> bool:
    """Test session creation and cleanup."""
    print("\n2. Testing session lifecycle...")

    # Create session
    try:
        r = await client.post(
            f"{base_url}/sessions",
            json={"system_prompt": "You are a helpful voice assistant. Keep responses brief."}
        )
        if r.status_code not in (200, 201):
            print(f"   Create failed: HTTP {r.status_code}")
            print(f"   Response: {r.text}")
            return False

        session = r.json()
        session_id = session.get("session_id")
        print(f"   Created session: {session_id}")

        # Get session
        r = await client.get(f"{base_url}/sessions/{session_id}")
        if r.status_code == 200:
            state = r.json().get("state", "unknown")
            print(f"   Session state: {state}")

        # Delete session
        r = await client.delete(f"{base_url}/sessions/{session_id}")
        if r.status_code in (200, 204):
            print("   Session deleted successfully")
            return True
        else:
            print(f"   Delete failed: HTTP {r.status_code}")
            return False

    except Exception as e:
        print(f"   Error: {e}")
        return False


async def test_llm_connection(client: httpx.AsyncClient, llm_url: str) -> bool:
    """Test direct LLM connection."""
    print("\n3. Testing LLM connection...")

    try:
        # Test /v1/models endpoint
        r = await client.get(f"{llm_url}/models", timeout=10.0)
        if r.status_code == 200:
            models = r.json()
            print(f"   LLM models available: {models}")
            return True
        else:
            print(f"   LLM returned: HTTP {r.status_code}")
            return False
    except httpx.ConnectError:
        print(f"   Cannot connect to LLM at {llm_url}")
        print("   Make sure vLLM is running on your cloud GPU")
        return False
    except Exception as e:
        print(f"   Error: {e}")
        return False


async def main():
    """Run all pipeline tests."""
    print("=" * 50)
    print("GoAssist Voice Pipeline Test")
    print("=" * 50)

    base_url = "http://localhost:8081"
    llm_url = "http://localhost:8000/v1"  # Default, override with cloud URL

    # Check for custom LLM URL from env
    import os
    if os.environ.get("LLM_BASE_URL"):
        llm_url = os.environ["LLM_BASE_URL"]

    print(f"\nGoAssist URL: {base_url}")
    print(f"LLM URL: {llm_url}")
    print()

    results = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Health
        results.append(("Health Check", await test_health(client, base_url)))

        # Test 2: Session lifecycle
        results.append(("Session Lifecycle", await test_session_lifecycle(client, base_url)))

        # Test 3: LLM connection
        results.append(("LLM Connection", await test_llm_connection(client, llm_url)))

    # Summary
    print("\n" + "=" * 50)
    print("Results:")
    print("=" * 50)

    passed = 0
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1

    print(f"\n{passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\nPipeline ready for voice testing!")
        print("\nNext steps:")
        print("  1. Add DEEPGRAM_API_KEY to .env for real ASR")
        print("  2. Set TTS_ENGINE=xtts-v2 for real TTS")
        print("  3. Connect a WebRTC client")
    else:
        print("\nSome tests failed. Check the output above.")
        if not results[2][1]:  # LLM failed
            print("\nLLM troubleshooting:")
            print("  - Verify your cloud GPU is running vLLM")
            print("  - Check LLM_BASE_URL in .env points to the correct URL")
            print("  - Try: curl $LLM_BASE_URL/models")

    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
