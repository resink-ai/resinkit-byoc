#!/bin/bash

function install_jupyter() {
    # copy resinkit_sample_project to /home/resinkit/
    cp -r "$ROOT_DIR/resources/jupyter/resinkit_sample_project" /home/resinkit/
    # copy jupyter_entrypoint.sh to /home/resinkit/.local/bin/
    mkdir -p /home/resinkit/.local/bin
    cp "$ROOT_DIR/resources/jupyter/jupyter_entrypoint.sh" /home/resinkit/.local/bin/
    chmod +x /home/resinkit/.local/bin/jupyter_entrypoint.sh
    chown -R resinkit:resinkit /home/resinkit/resinkit_sample_project
}

install_jupyter