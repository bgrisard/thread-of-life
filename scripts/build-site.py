"""Generate docs/ — a no-build static site GitHub Pages can serve directly.

Takes src/App.jsx, strips the module-only syntax Vite would otherwise handle,
and inlines it into a single HTML file that compiles JSX in the browser.
Copies public/data alongside it. Run after any change to src/App.jsx:

    python3 scripts/build-site.py
"""
import shutil, pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent
src = (root / "src" / "App.jsx").read_text(encoding="utf-8")

# The artifact/browser runtime has no module scope, so import.meta is invalid.
old_key = '''const API_KEY =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_ANTHROPIC_API_KEY) || "";
const HAS_KEY = !!API_KEY;
const IN_ARTIFACT = typeof window !== "undefined" && !!window.storage?.get;'''
new_key = '''const IN_ARTIFACT = typeof window !== "undefined" && !!window.storage?.get;
function getKey() {
  try { return localStorage.getItem("cr_key") || ""; } catch { return ""; }
}'''
if old_key not in src:
    sys.exit("build-site: key block not found — did src/App.jsx change shape?")
src = src.replace(old_key, new_key, 1)
src = src.replace('''    if (!HAS_KEY && !IN_ARTIFACT) throw new Error("NO_KEY");''',
                  '''    if (!getKey() && !IN_ARTIFACT) throw new Error("NO_KEY");''')
src = src.replace('Add VITE_ANTHROPIC_API_KEY to .env.local and restart to switch them on.',
                  'Open the Debug tab and paste an Anthropic API key to switch them on.')
src = src.replace('import React, { useState, useEffect, useRef, useCallback } from "react";',
                  'const { useState, useEffect, useRef, useCallback } = React;')
src = src.replace('export default function CrossReference()', 'function CrossReference()')

for bad in ("import.meta", "\nimport ", "\nexport "):
    if bad in src:
        sys.exit(f"build-site: {bad.strip()!r} still present — the page would fail to run")

html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="description" content="An endless, traceable thread through Scripture." />
<title>thread of life</title>
<style>html,body,#root{{height:100%;margin:0;background:#F1F1F3;overscroll-behavior:none}}</style>
<script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js" crossorigin></script>
</head>
<body>
<div id="root"></div>
<script type="text/babel" data-presets="react">
{src}
ReactDOM.createRoot(document.getElementById("root")).render(<CrossReference />);
</script>
</body>
</html>
'''

docs = root / "docs"
if docs.exists():
    shutil.rmtree(docs)
docs.mkdir()
(docs / "index.html").write_text(html, encoding="utf-8")
(docs / ".nojekyll").write_text("")          # stop Pages running Jekyll
shutil.copytree(root / "public" / "data", docs / "data")

kb = len(html) / 1024
files = sum(1 for _ in (docs / "data").rglob("*.json"))
print(f"docs/index.html  {kb:.0f} KB")
print(f"docs/data        {files} files")
print("docs/.nojekyll")
