#!/usr/bin/env node
// ساخت PDF جزوه: قطعه‌های پوشه‌ی lessons را به ترتیب نام کنار هم می‌گذارد،
// با Chromium چاپ می‌کند و هدر «رضا سلیمانی» را بالای همه‌ی صفحه‌ها می‌گذارد.
// شماره‌صفحه‌های فهرست در دو مرحله پر می‌شوند (مرحله‌ی اول فقط برای پیدا کردن صفحه‌ها).
//
//   node jozve/build.cjs            → output/jozve-farsi12.pdf
//   node jozve/build.cjs --preview  → به‌علاوه‌ی تصویر PNG صفحه‌ها در output/preview

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

let chromium;
try { ({ chromium } = require("playwright")); }
catch { ({ chromium } = require("/opt/node22/lib/node_modules/playwright")); }

const ROOT = __dirname;
const OUT_DIR = path.join(ROOT, "..", "output");
const PDF = path.join(OUT_DIR, "jozve-farsi12.pdf");
const HTML = path.join(ROOT, "_build.html");

const AUTHOR = "رضا سلیمانی";
const BOOK = "جزوه‌ی جامع فارسی دوازدهم";

const headerTemplate = `
<div style="width:100%;padding:6mm 14mm 0;font-family:'Vazirmatn FD';direction:rtl;-webkit-print-color-adjust:exact;">
  <div style="display:flex;align-items:center;justify-content:space-between;border-bottom:1.3px solid #b8892d;padding-bottom:1.4mm;">
    <div style="display:flex;align-items:center;gap:2.4mm;">
      <span style="display:inline-block;width:2.6mm;height:2.6mm;background:#b8892d;transform:rotate(45deg);border-radius:.5mm;"></span>
      <span style="font-size:13pt;font-weight:900;color:#1e3a5f;">${AUTHOR}</span>
    </div>
    <span style="font-size:8.5pt;font-weight:500;color:#7a8190;">${BOOK}</span>
  </div>
</div>`;

const footerTemplate = `
<div style="width:100%;padding:0 14mm 4mm;font-family:'Vazirmatn FD';direction:rtl;display:flex;justify-content:center;-webkit-print-color-adjust:exact;">
  <span style="font-size:8.5pt;font-weight:700;color:#1e3a5f;border:1px solid #e6dfd0;background:#fbf7ef;border-radius:3mm;padding:.2mm 4mm;">
    <span class="pageNumber"></span>
  </span>
</div>`;

const faDigits = s => String(s).replace(/\d/g, d => "۰۱۲۳۴۵۶۷۸۹"[d]);

function assemble(pageMap) {
  const dir = path.join(ROOT, "lessons");
  const parts = fs.readdirSync(dir).filter(f => f.endsWith(".html")).sort()
    .map(f => fs.readFileSync(path.join(dir, f), "utf8"));
  let html = fs.readFileSync(path.join(ROOT, "template.html"), "utf8")
    .replace("<!--CONTENT-->", parts.join("\n"));
  if (pageMap) {
    html = html.replace(/<span class="pg" data-for="([^"]+)"><\/span>/g,
      (m, id) => `<span class="pg" data-for="${id}">${faDigits(pageMap[id] ?? "")}</span>`);
  }
  fs.writeFileSync(HTML, html);
}

async function print(browser, out) {
  const page = await browser.newPage();
  await page.goto("file://" + HTML, { waitUntil: "load" });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({
    path: out, format: "A4", printBackground: true,
    displayHeaderFooter: true, headerTemplate, footerTemplate,
    margin: { top: "24mm", bottom: "15mm", left: "14mm", right: "14mm" },
  });
  await page.close();
}

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  execFileSync("python3", [path.join(ROOT, "jz2html.py")], { stdio: "inherit" });
  const browser = await chromium.launch();

  // مرحله‌ی ۱: پیدا کردن صفحه‌ی هر نشانگر فهرست
  assemble(null);
  const draft = path.join(OUT_DIR, "_draft.pdf");
  await print(browser, draft);
  const map = JSON.parse(execFileSync("python3", [path.join(ROOT, "pdftools.py"), "markers", draft]).toString().trim().split("\n").pop());
  fs.unlinkSync(draft);

  // مرحله‌ی ۲: خروجی نهایی با شماره‌صفحه‌های درست
  assemble(map);
  await print(browser, PDF);
  await browser.close();
  fs.unlinkSync(HTML);
  console.log("PDF:", PDF, "| markers:", JSON.stringify(map));

  if (process.argv.includes("--preview")) {
    console.log(execFileSync("python3", [path.join(ROOT, "pdftools.py"), "preview", PDF, path.join(OUT_DIR, "preview")]).toString());
  }
})();
