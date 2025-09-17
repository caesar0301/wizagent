"""Entry point for running MCP server as a module.

Usage:
    python -m wizagent.bu.mcp.server
"""

import asyncio

from wizagent.bu.mcp.server import main

if __name__ == "__main__":
    asyncio.run(main())
