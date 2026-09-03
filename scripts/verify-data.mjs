import fs from "fs";
const rd = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const idx = rd("data/index.json");
let verses = 0, links = 0, dangling = 0, missingBooks = [];
const all = {};
for (const b of idx.books) {
  const vp = `data/verses/${b.id}.json`, xp = `data/xrefs/${b.id}.json`;
  if (!fs.existsSync(vp) || !fs.existsSync(xp)) { missingBooks.push(b.id); continue; }
  all[b.id] = rd(vp);
  verses += Object.keys(all[b.id]).length;
}
for (const b of idx.books) {
  const x = rd(`data/xrefs/${b.id}.json`);
  for (const k in x) for (const [t] of x[k]) {
    links++;
    const [tb, tc, tv] = t.split(".");
    if (!all[tb]?.[`${tc}.${tv}`]) dangling++;
  }
}
console.log("books present:", idx.books.length - missingBooks.length, "of 66", missingBooks.length ? "MISSING " + missingBooks : "");
console.log("verses:", verses, "| index says:", idx.verses, verses === idx.verses ? "match" : "MISMATCH");
console.log("stored links (top 8):", links, "| dangling:", dangling);
console.log("translation:", idx.translation, "|", idx.license);
// spot checks
console.log("Gen 1:1  ->", all.GEN["1.1"]);
console.log("Isa 53:5 ->", all.ISA["53.5"].slice(0, 70) + "…");
console.log("omitted Matt 17:21 absent?", all.MAT["17.21"] === undefined);
// walk depth from Genesis 1:1
const xr = {}; for (const b of idx.books) xr[b.id] = rd(`data/xrefs/${b.id}.json`);
let cur = "GEN.1.1", seen = new Set(), steps = 0;
while (steps < 5000) {
  seen.add(cur);
  const [b, c, v] = cur.split(".");
  const refs = (xr[b][`${c}.${v}`] || []).map(r => r[0]).filter(k => !seen.has(k));
  if (!refs.length) break;
  cur = refs[0]; steps++;
}
console.log("unbroken walk from Genesis 1:1:", steps, "steps");
