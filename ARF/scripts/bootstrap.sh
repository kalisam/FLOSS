#!/bin/bash

set -e

# Install Rust toolchain and wasm target
rustup toolchain install stable --profile minimal --component clippy
rustup target add wasm32-unknown-unknown

# Build zomes
cargo build --release --target wasm32-unknown-unknown

# Hash DNA
hc dna pack dnas/rose_forest

echo "Bootstrap complete. You can now run 'bash scripts/launch.sh'"
