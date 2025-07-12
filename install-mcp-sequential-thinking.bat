@echo off
REM Sequential Thinking MCP Server Installation Script
REM This script helps install the Smithery AI Sequential Thinking MCP server

echo Installing Sequential Thinking MCP Server...

REM Create a directory for MCP servers
if not exist "%USERPROFILE%\.mcp-servers" mkdir "%USERPROFILE%\.mcp-servers"
cd /d "%USERPROFILE%\.mcp-servers"

REM Clone the Smithery MCP servers repository
if not exist "mcp-servers" (
    echo Cloning Smithery MCP servers repository...
    git clone https://github.com/smithery-ai/mcp-servers.git
)

cd mcp-servers

REM Install dependencies
echo Installing dependencies...
npm install

REM Build the servers
echo Building servers...
npm run build

echo Installation complete!
echo.
echo To use the Sequential Thinking MCP server, you can:
echo 1. Use the MCP extensions installed in VS Code
echo 2. Configure the server in your VS Code settings
echo 3. Access it through GitHub Copilot Chat
echo.
echo The server provides tools for dynamic and reflective problem-solving
echo through a structured thinking process.

pause
