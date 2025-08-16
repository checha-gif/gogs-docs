#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, zipfile, sys
from pathlib import Path
def load_manifest(path: Path):
    try:
        import yaml
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        place, section, src, dest = [], None, None, None
        for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = ln.strip()
            if s.startswith("place:"): section="place"; continue
            if section=="place":
                if s.startswith("-"):
                    if src and dest: place.append({"src":src,"dest":dest}); src=dest=None
                if s.startswith("src:"): src=s.split("src:",1)[1].strip()
                if s.startswith("dest:"): dest=s.split("dest:",1)[1].strip()
        if src and dest: place.append({"src":src,"dest":dest})
        return {"place": place}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--version", required=True); ap.add_argument("--out", default="dist")
    ap.add_argument("--name", default="release_bundle"); args=ap.parse_args()
    repo=Path(".").resolve(); mani=repo/"install_manifest.yaml"
    if not mani.exists(): print("ERROR: install_manifest.yaml not found", file=sys.stderr); sys.exit(2)
    manifest=load_manifest(mani)
    out_dir=repo/args.out; out_dir.mkdir(parents=True, exist_ok=True)
    zip_path=out_dir/f"{args.name}_v{args.version}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("install_manifest.yaml", mani.read_text(encoding="utf-8"))
        for ent in manifest.get("place",[]) or []:
            src=repo/ent.get("src","")
            if src.exists(): z.write(src, arcname=str(src))
    print(str(zip_path))
if __name__=="__main__": main()
