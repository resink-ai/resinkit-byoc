#!/bin/bash

# mount-s3 s3://resinkit-shared-data/ /mnt/resinkitshareddata
function debian_mount_s3_path() {

    if curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/ &>/dev/null; then
        echo "[RESINKIT] Running on EC2"
    else
        echo "[RESINKIT] Not running on EC2, skipping S3 mount setup"
        return 0
    fi

    # Use environment variables with fallbacks
    local BUCKET_NAME="${BUCKET_NAME:-resinkit-shared-data}"
    local MOUNT_POINT="${MOUNT_POINT:-/mnt/resinkitshareddata}"

    # Check if s3 path is already mounted
    if mount | grep -q "$MOUNT_POINT"; then
        echo "[RESINKIT] $MOUNT_POINT already mounted, skipping"
        return 0
    fi

    # Check if mount-s3 is already installed
    if ! command -v mount-s3 >/dev/null 2>&1; then
        echo "[RESINKIT] Installing mount-s3..."

        # Detect architecture
        ARCH=$(dpkg --print-architecture)
        if [ "$ARCH" = "amd64" ]; then
            MOUNT_S3_ARCH="x86_64"
        elif [ "$ARCH" = "arm64" ]; then
            MOUNT_S3_ARCH="arm64"
        else
            echo "[RESINKIT] Error: Unsupported architecture: $ARCH"
            return 1
        fi

        # Download and install mount-s3
        wget https://s3.amazonaws.com/mountpoint-s3-release/latest/${MOUNT_S3_ARCH}/mount-s3.deb -O /tmp/mount-s3.deb
        apt-get update
        apt-get install -y /tmp/mount-s3.deb
        rm -f /tmp/mount-s3.deb
    else
        echo "[RESINKIT] mount-s3 is already installed"
    fi

    # Create mount point if it doesn't exist
    if [ ! -d "$MOUNT_POINT" ]; then
        echo "[RESINKIT] Creating mount point $MOUNT_POINT"
        mkdir -p "$MOUNT_POINT"
    fi

    # Check if already mounted
    if mount | grep -q "$MOUNT_POINT"; then
        echo "[RESINKIT] $MOUNT_POINT is already mounted"
    else
        echo "[RESINKIT] Mounting with command: mount-s3 s3://$BUCKET_NAME/ $MOUNT_POINT"
        mount-s3 "s3://$BUCKET_NAME/" "$MOUNT_POINT" || {
            echo "[RESINKIT] Error: Failed to mount S3 path"
            return 1
        }
        echo "[RESINKIT] Successfully mounted S3 path"
    fi

    # Add to fstab if not already present (mount-s3 fstab entry)
    local FSTAB_ENTRY="s3://$BUCKET_NAME/ $MOUNT_POINT fuse.mount-s3 _netdev 0 0"
    if ! grep -q "$MOUNT_POINT" /etc/fstab; then
        echo "[RESINKIT] Adding mount to /etc/fstab for persistence"
        echo "$FSTAB_ENTRY" >>/etc/fstab
        echo "[RESINKIT] Added to fstab: $FSTAB_ENTRY"
    else
        echo "[RESINKIT] Mount point already exists in /etc/fstab"
    fi

    echo "[RESINKIT] S3 mount setup completed successfully"
}

debian_mount_s3_path
