#!/bin/bash

# === Configuration ===
INSTANCE_USER="ubuntu"  # Change this if your VM uses a different username
INSTANCE_IP="your-instance-public-ip"  # Replace with your VM's public IP
SSH_KEY_PATH="~/.ssh/id_rsa"  # Path to your private SSH key
PROJECT_DIR="houndthecult"  # Name of the project directory
REMOTE_DIR="/home/$INSTANCE_USER/$PROJECT_DIR"  # Remote directory on the VM

# === Functions ===

# Exit on error
set -e

# Print header for clarity
print_header() {
    echo "======================================="
    echo "$1"
    echo "======================================="
}

# === Deployment Steps ===

print_header "Step 1: Compress Project Files"
# Compress the project directory into a tarball for transfer
tar -czf ${PROJECT_DIR}.tar.gz ${PROJECT_DIR}

print_header "Step 2: Transfer Project Files to Oracle Instance"
# Use SCP to transfer the tarball to the remote instance
scp -i ${SSH_KEY_PATH} ${PROJECT_DIR}.tar.gz ${INSTANCE_USER}@${INSTANCE_IP}:${REMOTE_DIR}.tar.gz

print_header "Step 3: Connect to Instance and Set Up Environment"
# SSH into the instance and set up the environment
ssh -i ${SSH_KEY_PATH} ${INSTANCE_USER}@${INSTANCE_IP} << EOF
    set -e
    
    echo "Unpacking project files..."
    mkdir -p ${REMOTE_DIR}
    tar -xzf ${REMOTE_DIR}.tar.gz -C ${REMOTE_DIR}
    rm ${REMOTE_DIR}.tar.gz
    
    echo "Installing dependencies..."
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y python3 python3-pip screen
    
    echo "Installing Python dependencies..."
    pip3 install -r ${REMOTE_DIR}/requirements.txt
    
    echo "Setting up logging directory..."
    mkdir -p ${REMOTE_DIR}/logs
    
    echo "Deployment complete!"
EOF

print_header "Step 4: Start Bot in Screen Session"
# Start the bot in a detached screen session
ssh -i ${SSH_KEY_PATH} ${INSTANCE_USER}@${INSTANCE_IP} << EOF
    screen -dmS houndbot bash -c "
        cd ${REMOTE_DIR};
        python3 main.py;
        exec bash;
    "
EOF

print_header "Deployment Finished!"
echo "Your bot is now running on the Oracle Free Tier instance."
