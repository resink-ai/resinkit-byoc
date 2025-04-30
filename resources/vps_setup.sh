#!/bin/bash

# VPS Initial Setup Script (Debian/Ubuntu Focused)
# Run as root on a newly provisioned server.

# --- Configuration ---
# Consider changing this if you want SSH on a non-standard port
SSH_PORT="22"
# Set your desired timezone (e.g., "America/Los_Angeles", "Europe/London", "UTC")
# Leave empty to skip timezone setup
TIMEZONE="America/Los_Angeles" # <--- CHANGE THIS TO YOUR TIMEZONE if desired

# --- Script Safety ---
# Exit immediately if a command exits with a non-zero status.
set -e
# Treat unset variables as an error when substituting.
set -u
# Exit if any command in a pipeline fails
set -o pipefail

# --- Functions ---
log() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

error_exit() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
    exit 1
}

# --- Pre-checks ---
if [ "$(id -u)" -ne 0 ]; then
    error_exit "This script must be run as root."
fi

# Check if dialog is installed for better prompts, install if not
if ! command -v dialog > /dev/null; then
    log "Installing 'dialog' for better user interaction..."
    apt-get update > /dev/null
    apt-get install -y dialog > /dev/null
fi

# --- User Input ---
# Use dialog for better prompting if available, otherwise use read
if command -v dialog > /dev/null; then
    NEW_USERNAME=$(dialog --inputbox "Enter the username for the new sudo user:" 8 40 3>&1 1>&2 2>&3 3>&-)
    dialog --msgbox "You will now be asked to paste the SSH public key for the new user ($NEW_USERNAME).\n\nMake sure it's the PUBLIC key (usually ends with .pub) and includes the 'ssh-rsa' or 'ssh-ed25519' part." 10 60
    SSH_PUBLIC_KEY=$(dialog --inputbox "Paste the SSH public key for user '$NEW_USERNAME':" 12 70 3>&1 1>&2 2>&3 3>&-)
else
    read -rp "Enter the username for the new sudo user: " NEW_USERNAME
    echo "You will now be asked to paste the SSH public key for the new user ($NEW_USERNAME)."
    echo "Make sure it's the PUBLIC key (usually ends with .pub) and includes the 'ssh-rsa' or 'ssh-ed25519' part."
    read -rp "Paste the SSH public key for user '$NEW_USERNAME': " SSH_PUBLIC_KEY
fi


# Validate input
if [ -z "$NEW_USERNAME" ]; then
    error_exit "Username cannot be empty."
fi
if [ -z "$SSH_PUBLIC_KEY" ]; then
    error_exit "SSH public key cannot be empty."
fi
# Basic check if the key looks like a key (starts with ssh- or ecdsa-)
if ! [[ "$SSH_PUBLIC_KEY" =~ ^(ssh-rsa|ssh-dss|ssh-ed25519|ecdsa-sha2-nistp256|ecdsa-sha2-nistp384|ecdsa-sha2-nistp521) ]]; then
   log "Warning: Pasted public key doesn't look like a standard SSH key format. Proceeding anyway."
fi


# --- System Update ---
log "Updating package lists and upgrading system packages..."
apt-get update
# Avoid grub prompts during upgrade if possible
DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
log "System update complete."

# --- Install Essential Packages ---
log "Installing essential packages (sudo, ufw, fail2ban, curl, wget, git, unzip, htop, ncdu)..."
DEBIAN_FRONTEND=noninteractive apt-get install -y sudo ufw fail2ban curl wget git unzip htop ncdu
log "Essential packages installed."

# --- Set Timezone (Optional) ---
if [ -n "$TIMEZONE" ]; then
    log "Setting timezone to $TIMEZONE..."
    timedatectl set-timezone "$TIMEZONE"
    log "Timezone set."
else
    log "Skipping timezone setup."
fi

# --- Create New Sudo User ---
log "Creating new user '$NEW_USERNAME'..."
# Create user with home directory, default shell /bin/bash
if id "$NEW_USERNAME" &>/dev/null; then
    log "User '$NEW_USERNAME' already exists. Adding to sudo group if not already present."
else
    useradd -m -s /bin/bash "$NEW_USERNAME"
    log "User '$NEW_USERNAME' created."
fi

log "Adding user '$NEW_USERNAME' to the sudo group..."
usermod -aG sudo "$NEW_USERNAME"
log "Setting initial password for user '$NEW_USERNAME' (required for sudo)..."

echo "Please enter the password for user '$NEW_USERNAME':"
passwd "$NEW_USERNAME"
log "Password set for '$NEW_USERNAME'."

log "User '$NEW_USERNAME' added to sudo group."

# --- Configure SSH Key for New User ---
log "Setting up SSH key authentication for '$NEW_USERNAME'..."
USER_HOME=$(eval echo ~$NEW_USERNAME)
mkdir -p "$USER_HOME/.ssh"
echo "$SSH_PUBLIC_KEY" > "$USER_HOME/.ssh/authorized_keys"

# Set correct permissions
chmod 700 "$USER_HOME/.ssh"
chmod 600 "$USER_HOME/.ssh/authorized_keys"
chown -R "$NEW_USERNAME":"$NEW_USERNAME" "$USER_HOME/.ssh"
log "SSH key added and permissions set for '$NEW_USERNAME'."

# --- Secure SSH Daemon ---
log "Securing SSH configuration (/etc/ssh/sshd_config)..."
SSHD_CONFIG="/etc/ssh/sshd_config"

# Disable root login
log "Disabling root SSH login..."
sed -i -E 's/^#?PermitRootLogin\s+.*/PermitRootLogin no/' "$SSHD_CONFIG"

# Disable password authentication
log "Disabling password authentication (enforcing key-based)..."
sed -i -E 's/^#?PasswordAuthentication\s+.*/PasswordAuthentication no/' "$SSHD_CONFIG"
# Also disable ChallengeResponseAuthentication as it can sometimes allow password prompts
sed -i -E 's/^#?ChallengeResponseAuthentication\s+.*/ChallengeResponseAuthentication no/' "$SSHD_CONFIG"
# Make sure UsePAM is enabled if needed for other auth methods, but disable its password-related aspects if possible
# Note: Disabling PasswordAuthentication is usually sufficient. Check UsePAM if issues arise.
# sed -i -E 's/^#?UsePAM\s+.*/UsePAM yes/' "$SSHD_CONFIG" # Ensure UsePAM is enabled if needed

# Change SSH Port (Optional - uncomment if SSH_PORT is not 22)
# if [ "$SSH_PORT" != "22" ]; then
#     log "Changing SSH port to $SSH_PORT..."
#     sed -i -E "s/^#?Port\s+.*/Port $SSH_PORT/" "$SSHD_CONFIG"
# else
    log "Keeping SSH port as $SSH_PORT."
# fi

log "Validating SSH configuration..."
sshd -t
if [ $? -ne 0 ]; then
    error_exit "SSHD configuration validation failed. Please check /etc/ssh/sshd_config manually."
fi

log "Restarting SSH service..."
systemctl restart sshd
log "SSH service restarted."

# --- Configure Firewall (UFW) ---
log "Configuring firewall (UFW)..."
# Deny all incoming traffic by default
ufw default deny incoming
# Allow all outgoing traffic by default
ufw default allow outgoing

# Allow SSH traffic on the configured port
log "Allowing SSH traffic on port $SSH_PORT..."
ufw allow "$SSH_PORT/tcp"

# (Optional) Allow HTTP/HTTPS if this will be a web server
log "Allowing HTTP (port 80) and HTTPS (port 443)..."
ufw allow http
ufw allow https
ufw allow 8080/tcp

log "Enabling UFW firewall..."
# The 'y' is piped to answer the confirmation prompt non-interactively
echo "y" | ufw enable
ufw status verbose
log "UFW firewall configured and enabled."

# --- Enable and Start Fail2ban ---
log "Enabling and starting Fail2ban service..."
systemctl enable fail2ban
systemctl start fail2ban
log "Fail2ban service enabled and started."

# --- Final Instructions ---
echo ""
log "--- Initial Server Setup Complete ---"
log "Summary of changes:"
log " * System packages updated."
log " * Sudo user '$NEW_USERNAME' created."
log " * SSH access configured:"
log "   - Root login disabled."
log "   - Password authentication disabled (key-based only)."
log "   - SSH key added for user '$NEW_USERNAME'."
log " * Firewall (UFW) enabled and allows traffic on port $SSH_PORT/tcp."
log " * Fail2ban installed and running to protect against brute-force attacks."
log " * Basic utilities installed."
if [ -n "$TIMEZONE" ]; then log " * Timezone set to $TIMEZONE."; fi
echo ""
log "IMPORTANT: You should now log out of this root session."
log "Log back in using SSH as the new user:"
log "ssh $NEW_USERNAME@<your_vps_ip> -p $SSH_PORT -i /path/to/your/private_key"
echo ""
log "Test sudo access by running: sudo apt update"
echo ""

exit 0