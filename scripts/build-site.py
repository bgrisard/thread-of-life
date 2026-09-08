"""Generate docs/ — a no-build static site GitHub Pages can serve directly.

Takes src/App.jsx, strips the module-only syntax Vite would otherwise handle,
transpiles the JSX with esbuild, and writes a single HTML file plus the data.

The JSX is compiled here rather than in the browser on purpose. Babel's
in-browser React preset defaults to the automatic JSX runtime, which emits
`import { jsx } from "react/jsx-runtime"` — an import statement inside a
classic <script>, which the browser refuses, producing a blank page.

Requires node/npx (for esbuild). Run after any change to src/App.jsx:

    python3 scripts/build-site.py
"""
import shutil, pathlib, subprocess, sys, tempfile

root = pathlib.Path(__file__).resolve().parent.parent
src = (root / "src" / "App.jsx").read_text(encoding="utf-8")

# import.meta is only valid inside a module; the page is a classic script.
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
src = src.replace('import React, { useState, useEffect, useRef, useCallback } from "react";', '')
src = src.replace('export default function CrossReference()', 'function CrossReference()')

# React and ReactDOM arrive as globals from the UMD builds.
src = ('const { useState, useEffect, useRef, useCallback } = React;\n' + src +
       '\nReactDOM.createRoot(document.getElementById("root")).render(<CrossReference />);\n')

with tempfile.TemporaryDirectory() as tmp:
    jsx = pathlib.Path(tmp) / "app.jsx"
    out = pathlib.Path(tmp) / "app.js"
    jsx.write_text(src, encoding="utf-8")
    r = subprocess.run(
        ["npx", "--yes", "esbuild", str(jsx), "--loader:.jsx=jsx",
         "--jsx=transform", "--jsx-factory=React.createElement",
         "--jsx-fragment=React.Fragment", "--format=iife", "--target=es2020",
         f"--outfile={out}"],
        capture_output=True, text=True, shell=(sys.platform == "win32"),
    )
    if r.returncode != 0:
        sys.exit("build-site: esbuild failed\n" + r.stderr)
    js = out.read_text(encoding="utf-8")

for bad in ("import.meta", "\nimport ", "\nexport ", "react/jsx-runtime"):
    if bad in js:
        sys.exit(f"build-site: {bad.strip()!r} in output — the page would not run")

html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="description" content="An endless, traceable thread through Scripture." />
<title>thread of life</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Spectral:wght@400;600&display=swap" rel="stylesheet" />
<style>html,body,#root{{height:100%;margin:0;background:#F1F1F3;overscroll-behavior:none}}</style>
<script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
</head>
<body>
<div id="root"></div>
<script>
{js}
</script>
</body>
</html>
'''

docs = root / "docs"
if docs.exists():
    shutil.rmtree(docs)
docs.mkdir()
(docs / "index.html").write_text(html, encoding="utf-8")
(docs / ".nojekyll").write_text("")
shutil.copytree(root / "public" / "data", docs / "data")

print(f"docs/index.html  {len(html)/1024:.0f} KB (JSX precompiled, no Babel)")
print(f"docs/data        {sum(1 for _ in (docs / 'data').rglob('*.json'))} files")
print("docs/.nojekyll")
