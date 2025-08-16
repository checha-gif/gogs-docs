#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, zipfile, sys, shutil, hashlib, tempfile
from pathlib import Path
def unzip_to(path_zip: Path) -> Path:
    root = Path(tempfile.mkdtemp(prefix="bundle_unzip_"))
    with zipfile.ZipFile(path_zip, "r") as z: z.extractall(root)
    return root
def load_manifest(path: Path):
    try:
        import yaml
        with path.open("r", encoding="utf-8") as f: return yaml.safe_load(f)
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
def filehash(p: Path):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""): h.update(chunk)
    return h.hexdigest()
def copy_if_changed(src: Path, dst: Path, apply: bool):
    if not src.exists(): print(f"[ERR] Missing source: {src}"); return False, True
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        try:
            if filehash(src)==filehash(dst): print(f"[SKIP] {dst}"); return False, False
        except Exception: pass
        if apply: shutil.copy2(src, dst); print(f"[UPD] {dst}")
        else: print(f"[DRY] Would update {dst}")
        return True, False
    else:
        if apply: shutil.copy2(src, dst); print(f"[ADD] {dst}")
        else: print(f"[DRY] Would add {dst}")
        return True, False
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True); ap.add_argument("--repo", default=".")
    g=ap.add_mutually_exclusive_group(required=True); g.add_argument("--apply", action="store_true"); g.add_argument("--dry-run", action="store_true")
    args=ap.parse_args()
    bundle=Path(args.bundle).resolve(); repo=Path(args.repo).resolve()
    if not bundle.exists(): print("ERROR: bundle not found", file=sys.stderr); sys.exit(2)
    if not repo.exists(): print("ERROR: repo path not found", file=sys.stderr); sys.exit(2)
    root=unzip_to(bundle); mani=root/"install_manifest.yaml"
    if not mani.exists(): print("ERROR: install_manifest.yaml not found in bundle", file=sys.stderr); sys.exit(3)
    manifest=load_manifest(mani); changed=errors=0
    for ent in manifest.get("place",[]) or []:
        ch, er = copy_if_changed(root/ent.get("src",""), repo/ent.get("dest",""), args.apply)
        changed += int(ch); errors += int(er)
    print(f"\n[SUMMARY] {'Applied' if args.apply else 'Dry-run'}: {changed} changes. Errors: {errors}.")
    sys.exit(1 if errors and args.apply else 0)
if __name__=="__main__": main()
