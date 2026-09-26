"""تبدیل فایل‌های متنی ساده‌ی jozve/src/*.jz به HTML در jozve/lessons/.

قالب فایل‌ها (هر خط یک دستور):

  @id L01                  نشانگر فهرست
  @kicker ...              روتیتر سرِ درس
  @title ...               عنوان درس (نستعلیق)
  @chips a | b | c         برچسب‌های سرِ درس
  @card k=v | k=v          کارت شناسنامه
  @about ...               درون‌مایه (ردیف پهن کارت)
  @aboutk ...              برچسب ردیف پهن (پیش‌فرض: درون‌مایه)
  @num 1                   شماره‌ی بیت بعدی را از نو تنظیم می‌کند
  ## عنوان                 عنوان بخش
  ### عنوان                زیرعنوان نواری (گنج حکمت، شعرخوانی، ...)
  > مصراع ۱ // مصراع ۲     بیت (چند خط پشت‌سرهم = یک بلوک)
  >> متن نثر               بند نثر
  = معنی                   معنی بلوک
  z: / a: / f: / w: ...    برچسب‌های زبانی / ادبی / فکری / هشدار؛ جداکننده « ؛ »
  [box نوع عنوان] ... [/box]   جعبه (zabani adabi fekri tarikh warn tip)
  vocab:  (سپس خط‌های «واژه = معنی»)
  imla: و۱، و۲، ...
  wlist4 [شروع]  (سپس هر خط یک مدخل؛ فهرست شماره‌دار چندستونی تا خط خالی)
  table: س۱ | س۲  (سپس خط‌های «| خ۱ | خ۲»)
  qhead عنوان | زیرنویس
  qg نوع عنوان             گروه سؤال
  q: متن {بارم} [منبع]     سؤال؛ خط‌های «  > ...» نقل‌قول، «  opts: ...» گزینه‌ها، «  - ...» بند
  ans: ...                 پاسخ آخرین سؤال
  @answers                 پاسخ‌نامه‌ی سؤال‌های تا این‌جا
  ---                      صفحه‌ی جدید
  - مورد                   فهرست
  هر خط دیگر               پاراگراف
درون متن: **پررنگ**  ==هایلایت==  __زیرخط__
"""
import glob
import html
import os
import re
import sys

FA = "۰۱۲۳۴۵۶۷۸۹"
ICONS = {"zabani": "ز", "adabi": "ا", "fekri": "ف", "tarikh": "ت", "warn": "!", "tip": "★"}


def fa(n):
    return "".join(FA[int(c)] if c.isdigit() else c for c in str(n))


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"==(.+?)==", r'<span class="mark">\1</span>', s)
    s = re.sub(r"__(.+?)__", r"<u>\1</u>", s)
    return s


def tag(kind, text):
    text = text.strip()
    if not text:
        return ""
    m = re.match(r"^([^:]{1,40}):\s*(.+)$", text)
    if m:
        return f'<span class="tag {kind}"><b>{inline(m.group(1))}:</b> {inline(m.group(2))}</span>'
    return f'<span class="tag {kind}">{inline(text)}</span>'


class Doc:
    def __init__(self):
        self.out = []
        self.head = {}
        self.block = None      # بلوک بیت/نثر جاری
        self.verse_no = 0
        self.q_no = 0
        self.answers = []
        self.mode = None       # vocab / table / box
        self.buf = []
        self.list_open = False
        self.qg_open = False
        self.q_open = False

    # ---------- سرِ درس ----------
    def flush_head(self):
        if not self.head:
            return
        h = self.head
        self.head = {}
        chips = "".join(f"<span>{inline(c.strip())}</span>" for c in h.get("chips", "").split("|") if c.strip())
        mk = f'<span class="mk">@@{h["id"]}@@</span>' if "id" in h else ""
        self.out.append(
            '<div class="lesson-head"><svg class="pattern" width="100%" height="100%">'
            '<rect width="100%" height="100%" fill="url(#girih)"/></svg>'
            f'<div class="kicker">{inline(h.get("kicker", ""))}</div>'
            f'<h2>{inline(h.get("title", ""))}</h2><div class="meta">{chips}</div>{mk}</div>')
        if "card" in h or "about" in h:
            cells = []
            for kv in h.get("card", "").split("|"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    cells.append(f'<div><div class="k">{inline(k.strip())}</div><div class="v">{inline(v.strip())}</div></div>')
            n = max(1, len(cells))
            about = ""
            if "about" in h:
                about = f'<div class="wide"><div class="k">{h.get("aboutk", "درون‌مایه")}</div><div class="v">{inline(h["about"])}</div></div>'
            self.out.append(f'<div class="id-card" style="grid-template-columns:repeat({n},1fr)">{"".join(cells)}{about}</div>')

    # ---------- بلوک‌ها ----------
    def close_block(self):
        if self.block is None:
            return
        b = self.block
        self.block = None
        parts = ['<div class="verse-block">']
        for kind, content in b["lines"]:
            self.verse_no += 1
            n = f'<span class="n">{fa(self.verse_no)}</span>'
            if kind == "v":
                m1, _, m2 = content.partition("//")
                if m2.strip():
                    parts.append(f'<div class="verse">{n}<span class="m1">{inline(m1.strip())}</span><span class="m2">{inline(m2.strip())}</span></div>')
                else:
                    parts.append(f'<div class="verse single">{n}<span class="m1">{inline(m1.strip())}</span></div>')
            else:
                parts.append(f'<div class="prose">{n}{inline(content)}</div>')
        body = []
        if b["meaning"]:
            body.append(f'<div class="meaning">{inline(" ".join(b["meaning"]))}</div>')
        tags = "".join(b["tags"])
        if tags:
            body.append(f'<div class="notes">{tags}</div>')
        if body:
            parts.append(f'<div class="body">{"".join(body)}</div>')
        parts.append("</div>")
        self.out.append("".join(parts))

    def close_list(self):
        if self.list_open:
            self.out.append("</ul>")
            self.list_open = False

    def close_mode(self):
        if self.mode == "vocab":
            rows = self.buf
            half = (len(rows) + 1) // 2
            cols = [rows[:half], rows[half:]] if len(rows) > 5 else [rows]
            tables = []
            for col in cols:
                if not col:
                    continue
                trs = "".join(f'<tr><td class="w">{inline(w)}</td><td>{inline(m)}</td></tr>' for w, m in col)
                tables.append(f'<table class="vocab"><tr><th>واژه</th><th>معنی</th></tr>{trs}</table>')
            cls = "vocab-grid" if len(tables) > 1 else ""
            self.out.append(f'<div class="{cls}" style="margin-bottom:5mm">{"".join(tables)}</div>')
        elif self.mode == "table":
            head, *rows = self.buf
            ths = "".join(f"<th>{inline(c)}</th>" for c in head)
            trs = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            self.out.append(f'<table class="vocab grid-table"><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>')
        elif self.mode == "wlist":
            lis = "".join(f"<li>{inline(w)}</li>" for w in self.buf)
            self.out.append(f'<ol class="wlist" start="{self.wstart}" style="column-count:{self.wcols}">{lis}</ol>')
        self.mode = None
        self.buf = []

    def close_q(self):
        if self.q_open:
            self.out.append("</li>")
            self.q_open = False

    def close_qg(self):
        self.close_q()
        if self.qg_open:
            self.out.append("</ol></div>")
            self.qg_open = False

    def close_all(self):
        self.flush_head()
        self.close_block()
        self.close_list()
        self.close_mode()

    # ---------- خط به خط ----------
    def line(self, raw):
        s = raw.rstrip("\n")
        st = s.strip()

        if self.mode in ("vocab", "table", "wlist"):
            if not st:
                self.close_mode()
                return
            if self.mode == "wlist":
                self.buf.append(st)
            elif self.mode == "vocab":
                w, _, m = st.partition("=")
                self.buf.append((w.strip(), m.strip()))
            else:
                self.buf.append([c.strip() for c in st.strip("|").split("|")])
            return

        # سؤال‌ها: خط‌های تورفته متعلق به آخرین سؤال‌اند
        if self.q_open and s.startswith("  ") and st:
            if st.startswith(">"):
                self.out.append(f'<span class="quote">{inline(st[1:].strip())}</span>')
            elif st.startswith("opts:"):
                opts = [o.strip() for o in st[5:].split("|")]
                longest = max(len(o) for o in opts)
                cls = "opts four" if longest < 14 else "opts" if longest < 38 else "opts one"
                labels = ["۱", "۲", "۳", "۴", "۵", "۶"] if len(opts) == 4 and not st.startswith("opts:الف") else ["الف", "ب", "ج", "د", "هـ", "و"]
                if st.startswith("opts:الف"):
                    opts[0] = opts[0][3:].strip()
                self.out.append(f'<div class="{cls}">' + "".join(
                    f'<span data-n="{labels[i]}">{inline(o)}</span>' for i, o in enumerate(opts)) + "</div>")
            elif st.startswith("- "):
                self.out.append(f'<span class="sub">{inline(st[2:])}</span>')
            else:
                self.out.append(f'<span class="sub">{inline(st)}</span>')
            return

        if not st:
            self.close_block()
            self.close_list()
            self.close_q()
            return

        if st.startswith("@"):
            key, _, val = st[1:].partition(" ")
            if key == "num":
                self.close_block()
                self.verse_no = int(val.strip() or 1) - 1
                return
            if key == "answers":
                self.close_all()
                self.close_qg()
                if self.answers:
                    items = "".join(f'<div class="a"><b>{fa(n)}</b>{inline(a)}</div>' for n, a in self.answers)
                    self.out.append(f'<div class="section-title answers-title">پاسخ‌نامه</div><div class="answers">{items}</div>')
                self.answers = []
                return
            self.head[key] = val.strip()
            return

        if self.head:
            self.flush_head()

        if st == "---":
            self.close_all()
            self.close_qg()
            self.out.append('<div class="page-break"></div>')
            return

        if st.startswith("[box"):
            self.close_all()
            m = re.match(r"\[box\s+(\w+)\s*(.*)\]", st)
            kind, title = m.group(1), m.group(2)
            self.out.append(f'<div class="box {kind}"><div class="box-title"><span class="ico">{ICONS.get(kind, "•")}</span>{inline(title)}</div>')
            return
        if st == "[/box]":
            self.close_block()
            self.close_list()
            self.out.append("</div>")
            return

        if st.startswith("### "):
            self.close_all()
            self.close_qg()
            self.out.append(f'<div class="sub-head"><span>{inline(st[4:])}</span></div>')
            return
        if st.startswith("## "):
            self.close_all()
            self.close_qg()
            self.out.append(f'<div class="section-title">{inline(st[3:])}</div>')
            return

        if st.startswith(">>"):
            self.close_list()
            if self.block is None:
                self.block = {"lines": [], "meaning": [], "tags": []}
            elif self.block["meaning"] or self.block["tags"]:
                self.close_block()
                self.block = {"lines": [], "meaning": [], "tags": []}
            self.block["lines"].append(("p", st[2:].strip()))
            return
        if st.startswith(">"):
            self.close_list()
            if self.block is None or self.block["meaning"] or self.block["tags"]:
                self.close_block()
                self.block = {"lines": [], "meaning": [], "tags": []}
            self.block["lines"].append(("v", st[1:].strip()))
            return
        if st.startswith("= ") and self.block is not None:
            self.block["meaning"].append(st[2:].strip())
            return
        m = re.match(r"^([zafw]):\s*(.*)$", st)
        if m and self.block is not None:
            kind = {"z": "zabani", "a": "adabi", "f": "fekri", "w": "warn"}[m.group(1)]
            self.block["tags"].extend(tag(kind, t) for t in re.split(r"\s+؛\s+", m.group(2)))
            return

        if st == "vocab:":
            self.close_all()
            self.mode = "vocab"
            return
        if st.startswith("table:"):
            self.close_all()
            self.mode = "table"
            self.buf = [[c.strip() for c in st[6:].split("|")]]
            return
        if st.startswith("wlist"):
            self.close_all()
            self.mode = "wlist"
            parts = st.split()
            self.wcols = int(re.sub(r"\D", "", parts[0]) or 4)
            self.wstart = int(parts[1]) if len(parts) > 1 else 1
            self.buf = []
            return
        if st.startswith("imla:"):
            self.close_all()
            words = [w.strip() for w in re.split(r"[،,]", st[5:]) if w.strip()]
            self.out.append('<div class="imla">' + "".join(f"<span>{inline(w)}</span>" for w in words) + "</div>")
            return
        if st.startswith("ex:"):
            self.out.append(f'<span class="ex">{inline(st[3:].strip())}</span>')
            return

        if st.startswith("qhead"):
            self.close_all()
            self.close_qg()
            t, _, sub = st[5:].strip().partition("|")
            self.out.append(f'<div class="qbank-head"><h3>{inline(t.strip())}</h3><small>{inline(sub.strip())}</small></div>')
            return
        if st.startswith("qg "):
            self.close_all()
            self.close_qg()
            kind, _, title = st[3:].partition(" ")
            self.out.append(f'<div class="q-group {kind}"><span class="g">{inline(title)}</span><ol class="qs" style="--start:{self.q_no}">')
            self.qg_open = True
            return
        if st.startswith("q:"):
            self.close_all()
            self.close_q()
            body = st[2:].strip()
            score = src = ""
            m = re.search(r"\[([^\]]+)\]\s*$", body)
            if m:
                src, body = m.group(1), body[:m.start()].strip()
            m = re.search(r"\{([^}]+)\}\s*$", body)
            if m:
                score, body = m.group(1), body[:m.start()].strip()
            self.q_no += 1
            extra = ""
            if score:
                extra += f'<span class="score">{inline(score)}</span>'
            src_html = f'<span class="src">{inline(src)}</span>' if src else ""
            self.out.append(f"<li>{extra}{inline(body)}{src_html}")
            self.q_open = True
            return
        if st.startswith("ans:"):
            self.answers.append((self.q_no, st[4:].strip()))
            return

        if st.startswith("- "):
            self.close_block()
            if not self.list_open:
                self.out.append("<ul class=\"plain\">")
                self.list_open = True
            self.out.append(f"<li>{inline(st[2:])}</li>")
            return

        self.close_block()
        self.close_list()
        self.out.append(f"<p>{inline(st)}</p>")

    def finish(self):
        self.close_all()
        self.close_qg()
        return "\n".join(self.out)


def convert(path):
    d = Doc()
    for line in open(path, encoding="utf-8"):
        if line.lstrip().startswith("#!"):
            continue
        d.line(line)
    return f'<section class="page-break">\n{d.finish()}\n</section>\n'


if __name__ == "__main__":
    root = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(root, "lessons")
    for old in glob.glob(os.path.join(out_dir, "*.gen.html")):
        os.remove(old)
    files = sorted(glob.glob(os.path.join(root, "src", "*.jz")))
    for f in files:
        name = os.path.basename(f)[:-3] + ".gen.html"
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as o:
            o.write(convert(f))
    print(f"{len(files)} source files converted", file=sys.stderr)
