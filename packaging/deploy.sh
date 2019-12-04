#!/bin/bash

set -ex
cd "$TRAVIS_BUILD_DIR/packaging"

# Get the repo
git clone ssh://aur@aur.archlinux.org/bitwarden-pyro-git.git aur

# Update it
cp PKGBUILD aur
cd aur

# Change pkgver to current version
sed -i -r "s/^(pkgver)=(.*)$/\1=${VERSION}/g" PKGBUILD
sed -i -r "s/^(source=.*#tag)=(.*)$/\1=${TRAVIS_TAG}\")/g" PKGBUILD

# Create .SRCINFO
/bin/bash "$MAKEPKG_DIR/makepkg" --config="${MAKEPKG_CONF}" --printsrcinfo > .SRCINFO

# Commit
git add PKGBUILD .SRCINFO
git config user.email "deploy@mihalea.ro"
git config user.name "mihalea-deploy"
git commit -m "Release $TRAVIS_TAG"

# Deploy to AUR
git push origin master
