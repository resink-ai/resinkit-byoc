#!/bin/bash

# Minimal dev environment setup for a VPS (debian based)
# - intsall git vim curl wget
# - install zsh oh-my-zsh

apt-get update
apt-get install -y git vim curl wget zsh

# install oh-my-zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
