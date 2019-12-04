#!/bin/bash

# Check MAKEPKG_DIR
echo "MAKEPKG_DIR=$MAKEPKG_DIR"

# Get the package repo
git clone ssh://aur@aur.archlinux.org/bitwarden-pyro-git.git aur
cd aur

# Change pkgver to current version
sed -i -r "s/^(pkgver)=(.*)$/\1=${VERSION}/g" PKGBUILD
sed -i -r "s/^(source=.*#tag)=(.*)$/\1=${LATEST_TAG}\")/g" PKGBUILD

# Create SRC info
/bin/bash "$MAKEPKG_DIR/makepkg" --config="${MAKEPKG_CONF}" --printsrcinfo > test_src

echo "==== START .SRCINFO ===="
cat test_src
echo "====  END  .SRCINFO ===="