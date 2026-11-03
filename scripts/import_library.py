#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医学资料库导入器
遍历输入根目录下所有文档，按「书 -> 章 -> 节 -> 段落」切分，
输出到 <out>/  (manifest.json + books/<id>.json)。
支持断点续跑：已生成的书不再重复处理。

格式支持:
  .chm  -> hh.exe -decompile 解 HTML (Windows 原生)
  .docx -> python-docx
  .epub -> zip + bs4
  .pdf  -> PyMuPDF (仅可复制的；扫描版跳过，本机无 OCR)
  .txt  -> GBK/UTF-8 自动解码
跳过: .jpg .png .mp4 .mobi .doc(旧) .exe 以及无可抽取文字的 PDF

归类规则: 直接父目录名=分类，顶层目录名=分组；平铺文件用 --category。

用法:
  python import_library.py --root "D:/新资料" --out content
  python import_library.py --root "D:/新资料" --category 中医 --group 教材   # 全部归一类
  python import_library.py --root "D:/新资料" --max 20        # 试跑前 20 个
  python import_library.py --root "D:/新资料" --only "伤寒论"  # 只处理路径含某关键字
"""
import os, re, sys, json, subprocess, shutil, argparse, html as _html

ROOT = r"E:\医学"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "content")
BOOKS_DIR = os.path.join(OUT, "books")
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_chm_tmp")
_windir = os.environ.get("WINDIR", r"C:\Windows")
HH = None
for _cand in (os.path.join(_windir, "SysNative", "hh.exe"),
              os.path.join(_windir, "System32", "hh.exe"),
              "hh.exe"):
    if _cand == "hh.exe" or os.path.exists(_cand):
        HH = _cand
        break
if HH is None:
    HH = os.path.join(_windir, "System32", "hh.exe")

os.makedirs(BOOKS_DIR, exist_ok=True)

# ---------- 文本/结构抽取 ----------
def clean_text(s):
    s = s.replace("\u3000", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def is_toc_html(raw_html):
    """判断是否为 EPUB/CHM 的目录(TOC)页，避免把目录当正文"""
    if "kindle-cn-toc-level" in raw_html:
        return True
    if re.search(r'class\s*=\s*["\']toc', raw_html, re.I):
        return True
    if "sigil_toc_id" in raw_html:
        return True
    return False

def html_to_blocks(raw_html):
    """返回 [(tag, text)]，tag in h1/h2/h3/h4/p/title"""
    if is_toc_html(raw_html):
        return []
    from bs4 import BeautifulSoup
    # EPUB / XHTML 本质是 XML，用 xml 解析器更可靠（避免 HTML 解析告警与失配）
    head = raw_html.lstrip().lower()
    use_xml = head.startswith("<?xml") or "xhtml" in head[:300]
    parser = "xml" if use_xml else "lxml"
    try:
        soup = BeautifulSoup(raw_html, parser)
    except Exception:
        soup = BeautifulSoup(raw_html, "lxml")
    for tag in soup(["script", "style", "meta", "link"]):
        tag.decompose()
    blocks = []
    title = soup.title.get_text(strip=True) if soup.title else ""
    if title and title.lower() not in ("contents", "目录", "toc"):
        blocks.append(("title", title))
    # 按文档顺序取标题与段落
    for el in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]):
        txt = clean_text(el.get_text(" ", strip=True))
        if not txt:
            continue
        blocks.append((el.name, txt))
    if not blocks:
        # 退化：整页文本
        txt = clean_text(soup.get_text("\n"))
        for line in txt.split("\n"):
            line = line.strip()
            if line:
                blocks.append(("p", line))
    return blocks

def docx_to_blocks(path):
    """优先用 python-docx；损坏的 docx 退化到直接解包读 document.xml"""
    try:
        import docx
        d = docx.Document(path)
        blocks = []
        for p in d.paragraphs:
            txt = clean_text(p.text)
            if not txt:
                continue
            style = (p.style.name or "").lower()
            if style.startswith("heading") or style.startswith("标题"):
                m = re.match(r"heading\s*(\d)", style)
                lvl = int(m.group(1)) if m else 1
                blocks.append(("h%d" % min(lvl, 4), txt))
            else:
                blocks.append(("p", txt))
        if blocks:
            return blocks
    except Exception:
        pass
    # 退化：直接解析 xml
    try:
        import zipfile
        from lxml import etree
        z = zipfile.ZipFile(path)
        xml_name = "word/document.xml"
        if xml_name not in z.namelist():
            cands = [n for n in z.namelist() if n.endswith("document.xml")]
            if not cands:
                return []
            xml_name = cands[0]
        data = z.read(xml_name)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        root = etree.fromstring(data)
        body = root.find("w:body", ns)
        blocks = []
        for p in body.findall("w:p", ns):
            # 样式
            pstyle = p.find(".//w:pStyle", ns)
            lvl = 0
            if pstyle is not None:
                val = pstyle.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val") or ""
                m = re.match(r"(?i)heading\s*(\d)|标题(\d)", val)
                if m:
                    lvl = int(m.group(1) or m.group(2))
                elif re.match(r"(?i)title", val):
                    lvl = 0
            # 文本
            txt = "".join(t.text or "" for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"))
            txt = clean_text(txt)
            if not txt:
                continue
            if lvl:
                blocks.append(("h%d" % min(lvl, 4), txt))
            else:
                blocks.append(("p", txt))
        return blocks
    except Exception as e:
        print("   DOCX 解析失败:", e)
        return []

def epub_to_blocks(path):
    import zipfile, re as _re
    z = zipfile.ZipFile(path)
    names = [n for n in z.namelist()
             if n.lower().endswith((".xhtml", ".html", ".htm"))]
    # 按 spine 顺序更好，这里用文件名自然序近似
    def natkey(n):
        return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", n)]
    names.sort(key=natkey)
    blocks = []
    for n in names:
        try:
            data = z.read(n).decode("utf-8", "ignore")
        except Exception:
            continue
        for tag, txt in html_to_blocks(data):
            blocks.append((tag, txt))
    return blocks

def pdf_to_blocks(path):
    import fitz
    doc = fitz.open(path)
    blocks = []
    total = 0
    n_pages = doc.page_count
    for page in doc:
        t = page.get_text("text")
        total += len(t.strip())
        for line in t.split("\n"):
            line = clean_text(line)
            if line:
                blocks.append(("p", line))
    doc.close()
    return blocks, total, n_pages

def txt_to_blocks(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
        try:
            s = raw.decode(enc)
            break
        except Exception:
            s = None
    if s is None:
        return []
    blocks = []
    for line in s.split("\n"):
        line = clean_text(line)
        if line:
            blocks.append(("p", line))
    return blocks

def chm_to_blocks(path):
    import tempfile
    out = tempfile.mkdtemp(prefix="chm_")   # 每进程独立临时目录，支持并行
    try:
        subprocess.run([HH, "-decompile", out, path],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=180)
        files = []
        for root, _, fs in os.walk(out):
            for f in fs:
                if f.lower().endswith((".htm", ".html")):
                    files.append(os.path.join(root, f))
        def natkey(n):
            return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", n)]
        files.sort(key=natkey)
        blocks = []
        for f in files:
            try:
                data = open(f, "rb").read()
                # CHM 多为 GBK
                for enc in ("gb18030", "utf-8", "gbk"):
                    try:
                        data = data.decode(enc)
                        break
                    except Exception:
                        data = None
                if data is None:
                    continue
                for tag, txt in html_to_blocks(data):
                    blocks.append((tag, txt))
            except Exception:
                continue
        return blocks
    finally:
        shutil.rmtree(out, ignore_errors=True)

# ---------- 章节切分 ----------
CHAPTER_RE = re.compile(
    r"^(第[一二三四五六七八九十百千0-9]+[章卷篇回部]|"
    r"[卷篇]?[一二三四五六七八九十]+[、.．]|"
    r"卷[一二三四五六七八九十上中下]|"
    r"附录|前言|序言|引言|后记|跋|凡例|"
    r"chapter\s*\d|section\s*\d)",
    re.I)
SECTION_RE = re.compile(
    r"^(第[一二三四五六七八九十百千0-9]+[节]|"
    r"[（(][一二三四五六七八九十0-9]+[)）]|"
    r"[一二三四五六七八九十]+[、.．]|"
    r"\d+[.、．]|"
    r"[（(]\d+[)）])")

def heading_level(tag, text):
    t = text.strip()
    if CHAPTER_RE.match(t):
        return 1
    if tag in ("h1",) and len(t) < 40:
        return 1
    if SECTION_RE.match(t):
        return 2
    if tag in ("h2", "h3"):
        return 2
    if tag in ("h4", "h5", "h6"):
        return 3
    return 0

def split_to_chapters(blocks):
    chapters = []
    cur_ch = None
    cur_sec = None
    def new_ch(title):
        return {"title": title, "sections": []}
    def new_sec(title):
        return {"title": title, "paras": []}
    for tag, text in blocks:
        lvl = heading_level(tag, text)
        if lvl == 1:
            cur_ch = new_ch(text)
            chapters.append(cur_ch)
            cur_sec = None
        elif lvl == 2:
            if cur_ch is None:
                cur_ch = new_ch("正文")
                chapters.append(cur_ch)
            cur_sec = new_sec(text)
            cur_ch["sections"].append(cur_sec)
        else:
            if cur_ch is None:
                cur_ch = new_ch("正文")
                chapters.append(cur_ch)
            if cur_sec is None:
                cur_sec = new_sec("")
                cur_ch["sections"].append(cur_sec)
            cur_sec["paras"].append(text)
    # 清理空章/空节
    out = []
    for ch in chapters:
        secs = [s for s in ch["sections"] if s["paras"] or s["title"]]
        if secs:
            ch["sections"] = secs
            out.append(ch)
    return out

# ---------- 命名/分类 ----------
def slugify(s, maxlen=60):
    s = re.sub(r"[\\/:*?\"<>|%#.（）()《》“”‘’\s]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:maxlen]

def clean_category(name):
    name = name.strip()
    name = re.sub(r"^[0-9]+[.、\s]*", "", name)
    name = name.replace("《", "").replace("》", "")
    name = re.sub(r"(系列|丛刊|丛书)?\s*\d*\s*(套|本|册|卷)?$", "", name)
    name = re.sub(r"\d+套$|\d+本$|\d+册$", "", name)
    return name.strip(" -_")

KNOWN_MAP = {
    "JiaoCai": "中医教材",
    "ZhuZuo": "中医著作",
}

def classify(rel_parts, default_cat="导入", group=None):
    """rel_parts: 相对输入根目录的路径分段（不含文件名）。

    默认归类规则：
      - 直接父目录名 → 分类(category)
      - 顶层目录名   → 分组(group)
      - 平铺文件(无父目录) → 用 default_cat；group 非 None 时强制覆盖分组。
    例：root/中医/金匮要略/x.pdf → cat=金匮要略, grp=中医；root/内经/x.pdf → cat=内经, grp=内经。
    """
    if len(rel_parts) >= 2:
        parent = rel_parts[-2]
        top = rel_parts[0]
        cat = clean_category(parent) or default_cat
        grp = clean_category(top) if top != parent else cat
    else:
        cat = default_cat
        grp = group or default_cat
    if group:
        grp = group
    return cat, grp

def title_from_file(fname):
    t = re.sub(r"\.(chm|docx|doc|epub|pdf|txt|mobi)$", "", fname, flags=re.I)
    t = t.replace("《", "").replace("》", "")
    t = re.sub(r"^\d+[.、\s]*", "", t)
    t = re.sub(r"[_]+", " ", t).strip()
    return t or fname

# ---------- 主流程 ----------
def walk_files():
    res = []
    for root, _, fs in os.walk(ROOT):
        for f in fs:
            ext = f.lower().rsplit(".", 1)[-1] if "." in f else ""
            if ext in ("chm", "docx", "epub", "pdf", "txt"):
                res.append(os.path.join(root, f))
    # 稳定排序
    res.sort()
    return res

def make_bid(cat, title, done_ids):
    bid = slugify(f"{cat}_{title}")[:80]
    base, n = bid, 1
    while bid in done_ids:
        n += 1
        bid = f"{base}_{n}"
    return bid

def process_file(task):
    """处理单个文件。task=(path, cat, grp, title, bid)。返回 book dict 或 None(跳过)。
    顶层函数，供多进程池调用。"""
    path, cat, grp, title, bid = task
    try:
        ext = path.lower().rsplit(".", 1)[-1]
        if ext == "chm":
            blocks = chm_to_blocks(path)
        elif ext == "docx":
            blocks = docx_to_blocks(path)
        elif ext == "epub":
            blocks = epub_to_blocks(path)
        elif ext == "txt":
            blocks = txt_to_blocks(path)
        elif ext == "pdf":
            blocks, tot, npages = pdf_to_blocks(path)
            avg = (tot / npages) if npages else 0
            if tot < 200 or avg < 25:
                return None
        else:
            return None
        chapters = split_to_chapters(blocks)
        word_count = sum(len(s) for ch in chapters for sec in ch["sections"] for s in sec["paras"])
        if word_count < 80:
            return None
        return {
            "id": bid,
            "title": title,
            "category": cat,
            "group": grp,
            "source": path,
            "wordCount": word_count,
            "chapterCount": len(chapters),
            "chapters": chapters,
        }
    except Exception as e:
        print(f"   处理失败 {os.path.basename(path)}: {e}")
        return None

def main():
    global ROOT, OUT, BOOKS_DIR
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=ROOT, help="输入根目录（含待导入文档，默认 E:\\医学）")
    ap.add_argument("--out", default=OUT, help="输出目录（默认 memory-app/content）")
    ap.add_argument("--category", default="导入", help="平铺文件/无父目录时的默认分类名")
    ap.add_argument("--group", default=None, help="强制分组名（覆盖自动推断）")
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--only", type=str, default="")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()

    ROOT = args.root
    OUT = args.out
    BOOKS_DIR = os.path.join(OUT, "books")
    os.makedirs(BOOKS_DIR, exist_ok=True)

    files = walk_files()
    if args.only:
        files = [f for f in files if args.only in f]
    if args.max:
        files = files[:args.max]

    # 读已有 manifest 以续跑
    manifest_path = os.path.join(OUT, "manifest.json")
    manifest = []
    if os.path.exists(manifest_path):
        try:
            manifest = json.load(open(manifest_path, "r", encoding="utf-8"))
        except Exception:
            manifest = []
    done_ids = {m["id"] for m in manifest}

    # 构造任务，跳过已完成
    tasks = []
    for path in files:
        rel = os.path.relpath(path, ROOT).split(os.sep)
        cat, grp = classify(rel, default_cat=args.category, group=args.group)
        title = title_from_file(os.path.basename(path))
        bid = make_bid(cat, title, done_ids)
        done_ids.add(bid)   # 预占，避免并发重复
        tasks.append((path, cat, grp, title, bid))

    total = len(tasks)
    print(f"待处理文件: {total}（已完成 {len(manifest)} 本，续跑）")

    # 拆分 CHM（慢，并行）与其它（快，单线程）
    chm_tasks = [t for t in tasks if t[0].lower().endswith(".chm")]
    other_tasks = [t for t in tasks if not t[0].lower().endswith(".chm")]
    skipped = []

    def write_book(book):
        if book is None:
            return False
        with open(os.path.join(BOOKS_DIR, book["id"] + ".json"), "w", encoding="utf-8") as fp:
            json.dump(book, fp, ensure_ascii=False, separators=(",", ":"))
        manifest.append({
            "id": book["id"], "title": book["title"], "category": book["category"],
            "group": book["group"], "wordCount": book["wordCount"],
            "chapterCount": book["chapterCount"],
        })
        json.dump(manifest, open(manifest_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        return True

    # 其它格式单线程
    oc = 0
    for t in other_tasks:
        b = process_file(t)
        if write_book(b):
            oc += 1
            print(f"  [doc/epub/pdf/txt] {b['category']}/{b['title']} 章{b['chapterCount']} 字{b['wordCount']}")
        else:
            skipped.append(t[0])
    print(f"非CHM 完成 {oc} 本")

    # CHM 多进程并行
    cc = 0
    if chm_tasks:
        try:
            from multiprocessing import Pool
            with Pool(processes=args.workers) as pool:
                for i, b in enumerate(pool.imap_unordered(process_file, chm_tasks), 1):
                    if write_book(b):
                        cc += 1
                        if cc % 10 == 0:
                            print(f"  [chm] 进度 {cc}/{len(chm_tasks)} 当前 {b['category']}/{b['title']}")
                    else:
                        skipped.append("(chm跳过)")
        except Exception as e:
            print("CHM 并行失败，回退单线程:", e)
            for t in chm_tasks:
                b = process_file(t)
                if write_book(b):
                    cc += 1
    print(f"CHM 完成 {cc} 本")

    print("\n==== 完成 ====")
    print(f"成功生成: {len(manifest)} 本 | 本轮新增 {oc+cc} | 跳过/失败 {len(skipped)}")

if __name__ == "__main__":
    main()
