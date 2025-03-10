@echo off
echo Checking for Docker installation...

:: Check if Docker is installed
where docker >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Docker is not installed. Installing Docker...

    :: Download and install Docker silently
    powershell -Command "& {Invoke-WebRequest -UseBasicParsing -Uri 'https://desktop.docker.com/win/main/amd64/Docker Desktop Installer.exe' -OutFile 'DockerInstaller.exe'}"
    start /wait DockerInstaller.exe
    del DockerInstaller.exe

    echo Docker installed! Please restart your computer.
    exit /b
)

echo Running NetPilot Server...
docker-compose up -d
