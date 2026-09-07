#!/bin/bash
set -e
VER=1.0.0-1
ROOT=build/taskmanager-ubuntu_${VER}_all
rm -rf build
mkdir -p "$ROOT/DEBIAN" "$ROOT/usr/bin" "$ROOT/usr/share/taskmanager-ubuntu" "$ROOT/usr/share/applications" "$ROOT/usr/share/doc/taskmanager-ubuntu"
cp packaging/DEBIAN/control "$ROOT/DEBIAN/"
cp -r src "$ROOT/usr/share/taskmanager-ubuntu/"
find "$ROOT" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
printf '#!/bin/sh\nexec python3 -c "import sys; sys.path.insert(0, \x27/usr/share/taskmanager-ubuntu\x27); from src.app import main; main()" "$@"\n' > "$ROOT/usr/bin/taskmanager-ubuntu"
chmod 755 "$ROOT/usr/bin/taskmanager-ubuntu"
cp packaging/usr-share-applications/taskmanager-ubuntu.desktop "$ROOT/usr/share/applications/"
echo "taskmanager-ubuntu ($VER) - changelog inicial" | gzip -9 -c > "$ROOT/usr/share/doc/taskmanager-ubuntu/changelog.gz"
dpkg-deb --root-owner-group --build "$ROOT"
echo "OK: $ROOT.deb"
