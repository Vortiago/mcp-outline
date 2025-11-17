"""
Integration test for stdio mode logging behavior.

Verifies that when running in stdio mode, the server produces NO log output
on stdout or stderr that could interfere with the MCP JSON-RPC protocol.
"""

import asyncio
import json
import os
import subprocess

import pytest


@pytest.mark.integration
def test_stdio_mode_no_log_output():
    """
    Verify that stdio mode produces no non-JSON-RPC output.

    In stdio mode, the MCP protocol uses stdin/stdout for JSON-RPC
    communication. Any non-JSON-RPC output corrupts the protocol.

    Simple test strategy:
    1. Start server in stdio mode
    2. Let it run for a moment
    3. Check that stderr is completely empty
    4. Check that any stdout lines are valid JSON-RPC
    """
    # Start server as subprocess in stdio mode
    env = os.environ.copy()
    env["MCP_TRANSPORT"] = "stdio"

    process = subprocess.Popen(
        ["mcp-outline"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
    )

    try:
        # Give server time to start up
        # Any startup logs would appear during this time
        asyncio.run(asyncio.sleep(2))

        # Check if still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            pytest.fail(
                f"Server exited unexpectedly "
                f"(exit code {process.returncode})\n"
                f"stderr: {stderr}\nstdout: {stdout}"
            )

    finally:
        # Capture output
        if process.poll() is None:
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
        else:
            stdout, stderr = process.communicate()

    # CHECK 1: stderr must be completely empty (no logs allowed)
    assert not stderr.strip(), (
        f"stderr should be empty in stdio mode but got:\n{stderr}"
    )

    # CHECK 2: any stdout output must be valid JSON-RPC
    for line in stdout.strip().split("\n"):
        if not line.strip():
            continue

        # Try to parse as JSON
        try:
            msg = json.loads(line)
            # Must be a dict with jsonrpc field (or error/result)
            if isinstance(msg, dict):
                assert "jsonrpc" in msg or "result" in msg or "error" in msg, (
                    f"stdout line is not JSON-RPC: {line}"
                )
        except json.JSONDecodeError:
            # Any non-JSON output is a log message - fail the test
            pytest.fail(
                f"Found non-JSON output in stdout "
                f"(likely a log message):\n{line}\n"
                f"Full stdout:\n{stdout}"
            )


@pytest.mark.integration
def test_sse_mode_allows_log_output():
    """
    Verify that non-stdio modes (SSE) DO produce log output.

    This is the inverse test - ensuring that logging works properly
    in SSE/HTTP modes where logs are helpful for debugging.
    """
    # Start server in SSE mode
    env = os.environ.copy()
    env["MCP_TRANSPORT"] = "sse"

    process = subprocess.Popen(
        ["mcp-outline"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
    )

    try:
        # Give server time to start and log
        asyncio.run(asyncio.sleep(2))
    finally:
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()

    # In SSE mode, we SHOULD see startup logs
    combined_output = stdout + stderr

    assert "Starting MCP Outline server" in combined_output, (
        "SSE mode should produce startup logs"
    )

    assert "sse" in combined_output.lower(), (
        "SSE mode should mention transport mode in logs"
    )
