#!/bin/bash

# Check MAKEPKG_DIR
echo "MAKEPKG_DIR=$MAKEPKG_DIR"

# Package version 
version=$(git describe --long | sed 's/\([^-]*-g\)/r\1/;s/-/./g')
echo "version=${version}"

# Get the package repo
git clone ssh://aur@aur.archlinux.org/bitwarden-pyro-git.git aur
cd aur

# Create SRC info
/bin/bash "$MAKEPKG_DIR/makepkg" --config="${MAKEPKG_CONF}" --printsrcinfo > test_src

echo "==== START .SRCINFO ===="
cat test_src
echo "====  END  .SRCINFO ===="

echo "TRAVIS_TAG=${TRAVIS_TAG}"