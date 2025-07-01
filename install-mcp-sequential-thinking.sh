#!/bin/bash

# Sequential Thinking MCP Server Installation Script
# This script helps install the Smithery AI Sequential Thinking MCP server

echo "Installing Sequential Thinking MCP Server..."

# Create a directory for MCP servers
mkdir -p ~/.mcp-servers
cd ~/.mcp-servers

# Clone the Smithery MCP servers repository
if [ ! -d "mcp-servers" ]; then
    echo "Cloning Smithery MCP servers repository..."
    git clone https://github.com/smithery-ai/mcp-servers.git
fi

cd mcp-servers

# Install dependencies
echo "Installing dependencies..."
npm install

# Build the servers
echo "Building servers..."
npm run build

echo "Installation complete!"
echo ""
echo "To use the Sequential Thinking MCP server, you can:"
echo "1. Use the MCP extensions installed in VS Code"
echo "2. Configure the server in your VS Code settings"
echo "3. Access it through GitHub Copilot Chat"
echo ""
echo "The server provides tools for dynamic and reflective problem-solving"
echo "through a structured thinking process."
