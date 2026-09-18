#!/usr/bin/env bash
set -euo pipefail

INSTANCE_DIR="${MINECRAFT_INSTANCE_DIR:-$HOME/Documents/curseforge/minecraft/Instances/Reny Shaders Probe}"
INSTALL_DIR="${MINECRAFT_INSTALL_DIR:-$HOME/Documents/curseforge/minecraft/Install}"
JAVA_BIN="$INSTALL_DIR/java/jre-legacy/bin/java"
NATIVES_DIR="$INSTALL_DIR/natives/forge-10.13.4.1614"

# Generate classpath using python helper
CP=$(python3 -c "
import json
from pathlib import Path

install_dir = Path('$INSTALL_DIR')
forge_json = install_dir / 'versions/forge-10.13.4.1614/forge-10.13.4.1614.json'
mc_json = install_dir / 'versions/1.7.10/1.7.10.json'

with forge_json.open(encoding='utf-8') as f:
    forge_data = json.load(f)
with mc_json.open(encoding='utf-8') as f:
    mc_data = json.load(f)

cp_entries = []
for lib in forge_data.get('libraries', []) + mc_data.get('libraries', []):
    name = lib.get('name')
    parts = name.split(':')
    group, artifact, version = parts[0], parts[1], parts[2]
    classifier = parts[3] if len(parts) > 3 else None
    jar_name = f'{artifact}-{version}' + (f'-{classifier}' if classifier else '') + '.jar'
    rel_path = Path(*group.split('.')) / artifact / version / jar_name
    full_path = install_dir / 'libraries' / rel_path
    if full_path.exists():
        cp_entries.append(str(full_path))

cp_entries.append(str(install_dir / 'versions/forge-10.13.4.1614/forge-10.13.4.1614.jar'))
cp_entries.append(str(install_dir / 'versions/1.7.10/1.7.10.jar'))
print(':'.join(cp_entries))
")

mkdir -p "$INSTANCE_DIR/logs"

nohup "$JAVA_BIN" \
  -Djava.library.path="$NATIVES_DIR" \
  -cp "$CP" \
  -Xmx4096m -Xms512m \
  -Dfml.ignorePatchDiscrepancies=true \
  -Dfml.ignoreInvalidMinecraftCertificates=true \
  -DlibraryDirectory="$INSTALL_DIR/libraries" \
  -Duser.language=en \
  net.minecraft.launchwrapper.Launch \
  --username RenyTester \
  --version forge-10.13.4.1614 \
  --gameDir "$INSTANCE_DIR" \
  --assetsDir "$INSTALL_DIR/assets" \
  --assetIndex 1.7.10 \
  --uuid 00000000-0000-0000-0000-000000000000 \
  --accessToken 0 \
  --userProperties "{}" \
  --userType legacy \
  --tweakClass cpw.mods.fml.common.launcher.FMLTweaker \
  --width 1280 --height 720 \
  >> "$INSTANCE_DIR/logs/client_stdout.log" 2>&1 &

echo "Minecraft probe client launched in background."
