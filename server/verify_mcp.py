#!/usr/bin/env python3
"""
MCP Server Verification Script

This script verifies that the Property Management MCP server is correctly
configured and ready for deployment to Dedalus or other MCP clients.
"""

import subprocess
import sys
import json
import time
from pathlib import Path


def check_environment():
    """Check that the environment is properly configured"""
    print("=" * 60)
    print("MCP Server Verification")
    print("=" * 60)
    print()

    errors = []
    warnings = []

    # Check Python version
    print("✓ Checking Python version...")
    if sys.version_info < (3, 13):
        errors.append(f"Python 3.13+ required, found {sys.version_info.major}.{sys.version_info.minor}")
    else:
        print(f"  Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # Check UV is available
    print("\n✓ Checking UV package manager...")
    try:
        result = subprocess.run(["uv", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  {result.stdout.strip()}")
        else:
            errors.append("UV package manager not found. Install from astral.sh/uv")
    except FileNotFoundError:
        errors.append("UV package manager not found. Install from astral.sh/uv")

    # Check .env file exists
    print("\n✓ Checking configuration...")
    env_file = Path(".env")
    if not env_file.exists():
        warnings.append(".env file not found. Copy from .env.example and configure.")
    else:
        print("  .env file found")

    # Check main.py exists
    main_file = Path("main.py")
    if not main_file.exists():
        errors.append("main.py not found. Are you in the correct directory?")
    else:
        print("  main.py found")

    # Check mcp_config.json exists
    config_file = Path("mcp_config.json")
    if not config_file.exists():
        warnings.append("mcp_config.json not found")
    else:
        print("  mcp_config.json found")

    return errors, warnings


def test_imports():
    """Test that all required imports work"""
    print("\n✓ Testing imports...")

    errors = []

    try:
        import mcp
        print("  ✓ mcp package")
    except ImportError as e:
        errors.append(f"mcp package not installed: {e}")

    try:
        import sentence_transformers
        print("  ✓ sentence-transformers")
    except ImportError as e:
        errors.append(f"sentence-transformers not installed: {e}")

    try:
        import pymilvus
        print("  ✓ pymilvus")
    except ImportError as e:
        errors.append(f"pymilvus not installed: {e}")

    try:
        import httpx
        print("  ✓ httpx")
    except ImportError as e:
        errors.append(f"httpx not installed: {e}")

    try:
        import dotenv
        print("  ✓ python-dotenv")
    except ImportError as e:
        errors.append(f"python-dotenv not installed: {e}")

    return errors


def test_mcp_protocol():
    """Test that the server responds to MCP protocol"""
    print("\n✓ Testing MCP protocol...")

    try:
        # Create a simple initialize request
        initialize_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            },
            "id": 1
        }

        # Run the server with the initialize request
        proc = subprocess.Popen(
            ["uv", "run", "python", "main.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Send initialize request and get response
        stdout, stderr = proc.communicate(
            input=json.dumps(initialize_request) + "\n",
            timeout=30
        )

        # Check if we got a valid response
        if "result" in stdout or "serverInfo" in stdout:
            print("  ✓ Server responds to MCP protocol")
            return []
        else:
            return ["Server did not return valid MCP response"]

    except subprocess.TimeoutExpired:
        proc.kill()
        return ["Server timeout - took too long to respond"]
    except Exception as e:
        return [f"Error testing MCP protocol: {e}"]


def test_server_startup():
    """Test that the server starts without errors"""
    print("\n✓ Testing server startup...")

    try:
        # Start server and check it doesn't crash immediately
        proc = subprocess.Popen(
            ["uv", "run", "python", "main.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Wait a moment to see if it crashes
        time.sleep(2)

        if proc.poll() is None:
            # Still running, send SIGTERM
            proc.terminate()
            proc.wait(timeout=5)
            print("  ✓ Server starts successfully")
            return []
        else:
            # Process exited
            _, stderr = proc.communicate()
            return [f"Server exited immediately: {stderr}"]

    except Exception as e:
        return [f"Error testing startup: {e}"]


def print_summary(all_errors, all_warnings):
    """Print summary of checks"""
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    if all_errors:
        print("\n❌ ERRORS:")
        for error in all_errors:
            print(f"  - {error}")

    if all_warnings:
        print("\n⚠️  WARNINGS:")
        for warning in all_warnings:
            print(f"  - {warning}")

    if not all_errors and not all_warnings:
        print("\n✅ All checks passed!")
        print("\nServer is ready for deployment to Dedalus.")
        print("\nNext steps:")
        print("  1. Configure .env with your credentials")
        print("  2. Start Milvus: docker run -d -p 19530:19530 milvusdb/milvus:latest")
        print("  3. Add server to Dedalus MCP configuration")
        print("  4. Test from Dedalus client")
        return True
    elif not all_errors:
        print("\n✅ No critical errors")
        print("⚠️  Please address warnings before deploying")
        return True
    else:
        print("\n❌ Please fix errors before deploying")
        return False


def main():
    """Run all verification checks"""
    all_errors = []
    all_warnings = []

    # Environment checks
    errors, warnings = check_environment()
    all_errors.extend(errors)
    all_warnings.extend(warnings)

    if not all_errors:  # Only continue if environment is OK
        # Import checks
        errors = test_imports()
        all_errors.extend(errors)

        if not all_errors:  # Only test server if imports work
            # Server startup test
            errors = test_server_startup()
            all_errors.extend(errors)

            # MCP protocol test
            errors = test_mcp_protocol()
            all_errors.extend(errors)

    # Print summary
    success = print_summary(all_errors, all_warnings)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
