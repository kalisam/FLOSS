#!/bin/bash

set -e

# Clean up previous conductor runs
hc sandbox clean

# Initialize a new sandbox conductor
hc sandbox generate conductor-config.yaml

# Add agents to the conductor
hc sandbox add-agent agent1
hc sandbox add-agent agent2

# Install the DNA for agent1
hc sandbox call-admin agent1 install-app --path dnas/rose_forest/rose_forest.dna --agent-pub-key agent1 --installed-app-id rose-forest-app

# Activate the app for agent1
hc sandbox call-admin agent1 activate-app --installed-app-id rose-forest-app

# Install the DNA for agent2
hc sandbox call-admin agent2 install-app --path dnas/rose_forest/rose_forest.dna --agent-pub-key agent2 --installed-app-id rose-forest-app

# Activate the app for agent2
hc sandbox call-admin agent2 activate-app --installed-app-id rose-forest-app

# Start the conductor
hc sandbox run

echo "Holochain conductor launched with two agents and Rose Forest DNA installed."