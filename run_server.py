#!/usr/bin/env python
"""
TruthLens MCP Server launcher script
This script properly initializes and runs the MCP server.
"""

import sys
import os
from mcp.server import run_server

# Import our server definition
import main

if __name__ == "__main__":
    print("Starting TruthLens MCP Server...")
    # Run the server with the MCP instance defined in main.py
    run_server(main.mcp)