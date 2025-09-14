#!/bin/bash

# NetPilot Backend Deployment Script
# Copies backend files to VM at /root/netpilot-commands-server-new/

# VM Credentials (hardcoded for local use)
CLOUD_VM_IP="34.38.207.87"
CLOUD_VM_USER="netpilot-agent"
CLOUD_VM_PASSWORD="agent"
REMOTE_PATH="~/netpilot-commands-server-new"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting NetPilot Backend Deployment to VM${NC}"
echo "VM: ${CLOUD_VM_USER}@${CLOUD_VM_IP}"
echo "Remote Path: ${REMOTE_PATH}"
echo ""

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo -e "${RED}❌ sshpass is not installed. Please install it first:${NC}"
    echo "Ubuntu/Debian: sudo apt-get install sshpass"
    echo "macOS: brew install hudochenkov/sshpass/sshpass"
    echo "CentOS/RHEL: sudo yum install sshpass"
    exit 1
fi

# Check if scp is available
if ! command -v scp &> /dev/null; then
    echo -e "${RED}❌ scp is not available. Please install OpenSSH client.${NC}"
    exit 1
fi

# Create remote directory
echo -e "${YELLOW}📁 Creating remote directory...${NC}"
sshpass -p "${CLOUD_VM_PASSWORD}" ssh -o StrictHostKeyChecking=no "${CLOUD_VM_USER}@${CLOUD_VM_IP}" "mkdir -p ${REMOTE_PATH}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Remote directory created successfully${NC}"
else
    echo -e "${RED}❌ Failed to create remote directory${NC}"
    exit 1
fi

# Copy core folders
echo -e "${YELLOW}📦 Copying core folders...${NC}"

# Copy endpoints folder
echo "Copying endpoints/..."
sshpass -p "${CLOUD_VM_PASSWORD}" scp -o StrictHostKeyChecking=no -r endpoints/ "${CLOUD_VM_USER}@${CLOUD_VM_IP}:${REMOTE_PATH}/"

# Copy managers folder
echo "Copying managers/..."
sshpass -p "${CLOUD_VM_PASSWORD}" scp -o StrictHostKeyChecking=no -r managers/ "${CLOUD_VM_USER}@${CLOUD_VM_IP}:${REMOTE_PATH}/"

# Copy services folder
echo "Copying services/..."
sshpass -p "${CLOUD_VM_PASSWORD}" scp -o StrictHostKeyChecking=no -r services/ "${CLOUD_VM_USER}@${CLOUD_VM_IP}:${REMOTE_PATH}/"

# Copy utils folder
echo "Copying utils/..."
sshpass -p "${CLOUD_VM_PASSWORD}" scp -o StrictHostKeyChecking=no -r utils/ "${CLOUD_VM_USER}@${CLOUD_VM_IP}:${REMOTE_PATH}/"

# Copy logs folder
echo "Copying logs/..."
sshpass -p "${CLOUD_VM_PASSWORD}" scp -o StrictHostKeyChecking=no -r logs/ "${CLOUD_VM_USER}@${CLOUD_VM_IP}:${REMOTE_PATH}/"

# Copy individual files
echo -e "${YELLOW}📄 Copying individual files...${NC}"

# Copy requirements.txt
echo "Copying requirements.txt..."
sshpass -p "${CLOUD_VM_PASSWORD}" scp -o StrictHostKeyChecking=no requirements.txt "${CLOUD_VM_USER}@${CLOUD_VM_IP}:${REMOTE_PATH}/"

# Copy server.py
echo "Copying server.py..."
sshpass -p "${CLOUD_VM_PASSWORD}" scp -o StrictHostKeyChecking=no server.py "${CLOUD_VM_USER}@${CLOUD_VM_IP}:${REMOTE_PATH}/"

# Copy .env files (if they exist)
echo "Copying .env files..."
if [ -f .env ]; then
    sshpass -p "${CLOUD_VM_PASSWORD}" scp -o StrictHostKeyChecking=no .env "${CLOUD_VM_USER}@${CLOUD_VM_IP}:${REMOTE_PATH}/"
    echo "✅ .env copied"
else
    echo -e "${YELLOW}⚠️  .env file not found in current directory${NC}"
fi

if [ -f .env.local ]; then
    sshpass -p "${CLOUD_VM_PASSWORD}" scp -o StrictHostKeyChecking=no .env.local "${CLOUD_VM_USER}@${CLOUD_VM_IP}:${REMOTE_PATH}/"
    echo "✅ .env.local copied"
else
    echo -e "${YELLOW}⚠️  .env.local file not found in current directory${NC}"
fi

# Verify deployment
echo -e "${YELLOW}🔍 Verifying deployment...${NC}"
sshpass -p "${CLOUD_VM_PASSWORD}" ssh -o StrictHostKeyChecking=no "${CLOUD_VM_USER}@${CLOUD_VM_IP}" "ls -la ${REMOTE_PATH}"

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. SSH into your VM: ssh ${CLOUD_VM_USER}@${CLOUD_VM_IP}"
echo "2. Navigate to: cd ${REMOTE_PATH}"
echo "3. Install dependencies: pip install -r requirements.txt"
echo "4. Run the server: python server.py"
echo ""
echo -e "${YELLOW}📚 For production deployment instructions, see:${NC}"
echo -e "${GREEN}   backend/MANUAL_DEPLOYMENT_GUIDE.md${NC}"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
