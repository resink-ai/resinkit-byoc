#!/bin/bash

# Minimal dev environment setup for a VPS (debian based)
# - intsall git vim curl wget
# - install zsh oh-my-zsh

apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends git vim curl wget zsh ca-certificates kafkacat make unzip

# install oh-my-zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
