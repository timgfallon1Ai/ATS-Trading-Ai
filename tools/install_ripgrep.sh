#!/usr/bin/env bash
set -euo pipefail

# Repo-local ripgrep installer (no sudo, no Homebrew).
# Installs to: tools/bin/rg

RG_VERSION_DEFAULT="14.1.1"
RG_VERSION="${RG_VERSION:-$RG_VERSION_DEFAULT}"

repo_root() {
  cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd
}

ROOT="$(repo_root)"
BIN_DIR="$ROOT/tools/bin"
CACHE_DIR="$ROOT/tools/.cache"

mkdir -p "$BIN_DIR" "$CACHE_DIR"

uname_s="$(uname -s)"
uname_m="$(uname -m)"

if [[ "$uname_s" != "Darwin" ]]; then
  echo "This installer currently supports macOS only (Darwin). Detected: $uname_s" >&2
  exit 1
fi

case "$uname_m" in
  arm64) triple="aarch64-apple-darwin" ;;
  x86_64) triple="x86_64-apple-darwin" ;;
  *)
    echo "Unsupported architecture: $uname_m" >&2
    exit 1
    ;;
 esac

asset="ripgrep-${RG_VERSION}-${triple}.tar.gz"
url="https://github.com/BurntSushi/ripgrep/releases/download/${RG_VERSION}/${asset}"

cd "$CACHE_DIR"
rm -rf "ripgrep-${RG_VERSION}-${triple}" "$asset" || true

echo "Downloading ${url}"
curl -fL "$url" -o "$asset"

tar -xzf "$asset"

src_dir="$CACHE_DIR/ripgrep-${RG_VERSION}-${triple}"
if [[ ! -x "$src_dir/rg" ]]; then
  echo "Expected rg binary not found at: $src_dir/rg" >&2
  exit 1
fi

install -m 0755 "$src_dir/rg" "$BIN_DIR/rg"

"$BIN_DIR/rg" --version

echo ""
echo "Installed: $BIN_DIR/rg"
echo "Tip: add tools/bin to PATH (optional):"
echo "  export PATH=\"$ROOT/tools/bin:$PATH\""
