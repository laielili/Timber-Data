"""Publish `static/new/dist` into `docs/` for the static prototype.

Replaces the manual copy that had three recurring failure modes:

1. the built `index.html` points at `/assets/...`, which 404s when the site is
   served from a sub-path — it must be rewritten to `./assets/...`;
2. the asset filenames are content-hashed, so hand-editing the `<script src>`
   means guessing a hash (and silently shipping a dead page when you guess wrong);
3. copying over `docs/` wipes the hand-maintained shell — the floating demo pill
   and the capture-phase nav hook. Those now live in `scripts/_docs_shell.html`
   and are spliced back in automatically.

`docs/ai-workflow.html` is NOT in the build output, so it is left untouched —
this script only writes files that Vite produced.

    python scripts/_deploy_docs.py
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "static" / "new" / "dist"
DOCS = ROOT / "docs"
SHELL = Path(__file__).resolve().parent / "_docs_shell.html"

HEAD_ANCHOR = "</head>"
BODY_ANCHOR = "</body>"


def main() -> None:
    shell = SHELL.read_text(encoding="utf-8")
    if "<!--SPLIT-->" not in shell:
        raise SystemExit(f"{SHELL.name} is missing the <!--SPLIT--> marker")
    head_extra, body_extra = (part.strip("\n") for part in shell.split("<!--SPLIT-->"))

    # 1. assets: copy the new hashed files, then drop anything not in the build
    DOCS.mkdir(exist_ok=True)
    (DOCS / "assets").mkdir(exist_ok=True)
    built = {p.name for p in (DIST / "assets").iterdir() if p.is_file()}
    for name in built:
        shutil.copy2(DIST / "assets" / name, DOCS / "assets" / name)
    for stale in (DOCS / "assets").iterdir():
        if stale.is_file() and stale.name not in built:
            stale.unlink()
            print(f"  removed stale asset {stale.name}")

    # 2. index.html: relative asset paths + the hand-maintained shell
    html = (DIST / "index.html").read_text(encoding="utf-8")
    html, n_rel = re.subn(r'(["\'])/assets/', r"\1./assets/", html)
    if n_rel == 0:
        raise SystemExit("no /assets/ references found — did the Vite output change?")
    for anchor, extra in ((HEAD_ANCHOR, head_extra), (BODY_ANCHOR, body_extra)):
        if anchor not in html:
            raise SystemExit(f"{anchor} not found in the built index.html")
        html = html.replace(anchor, extra + "\n  " + anchor, 1)
    (DOCS / "index.html").write_text(html, encoding="utf-8")

    refs = re.findall(r'\./assets/([^"\']+)', html)
    missing = [r for r in refs if not (DOCS / "assets" / r).exists()]
    if missing:
        raise SystemExit(f"index.html references missing assets: {missing}")
    print(f"  rewrote {n_rel} asset path(s); index.html references {refs}")
    print(f"deployed {len(built)} asset(s) into {DOCS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
