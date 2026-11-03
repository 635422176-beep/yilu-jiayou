# -*- coding: utf-8 -*-
"""
卡片构建器：把 content/books 下的散文书，按「章节/知识点」切成卡片。
设计原则（用户 2026-11-03 明确）：
  1) 剔除前言/序/凡例/目录/编者/出版社/版权等废信息；
  2) 每张「节」= 一张知识点卡（不强行判歌诀、不嵌歌诀卡）；
     仅当节标题显式含 歌/诀/方歌/汤头/口诀 等，才标为「歌诀」类型。
输出：
  content/cards/<bookId>.cards.json   每本书的卡片数组
  content/all_cards.json               全部卡片（小程序/桌面共用）
卡片 schema:
  { id, bookId, bookTitle, group, category,
    chapterTitle, sectionTitle, name, type:'knowledge'|'mnemonic',
    front, back, tags:[], level1, level2, level3 }
用法：
  python scripts/build_cards.py                 # 全量(当前 manifest)
  python scripts/build_cards.py --group 吴雄志   # 仅某组(试点)
"""
import json, os, re, argparse, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_DIR = os.path.join(ROOT, "content", "books")
MANIFEST = os.path.join(ROOT, "content", "manifest.json")
CARDS_DIR = os.path.join(ROOT, "content", "cards")
ALL_CARDS = os.path.join(ROOT, "content", "all_cards.json")

NUM_RE = re.compile(r"^\s*[（(]?[一二三四五六七八九十百零\d]+[)）、.．\s]+")
# 废章节标题（整章/整节跳过）
FRONT_TITLE_RE = re.compile(r"(前言|凡例|目录|编者|出版|弁言|引语|校注说明|版权所有|序言|修订说明|内容提要)")
FRONT_TITLE_EXACT = {"正文", "序", "跋", "后记", "说明", "凡例", "目录", "附记"}
# 正文内偶发的出版/版权行（段级剔除）
PARA_SKIP_RE = re.compile(r"(ISBN|出版社|版权所有|印数|定价[:：]|版次|印次|责任编辑|封面设计|千字|字数[:：]|\bCIP\b)")
MNEMONIC_TITLE = re.compile(r"(歌|诀|方歌|汤头|口诀|诵读|背诵|七言|五言)")


def strip_num(t):
    if not t:
        return t
    return NUM_RE.sub("", t).strip(" 、.．")


def is_front_title(t):
    t = (t or "").strip()
    if t in FRONT_TITLE_EXACT:
        return True
    return bool(FRONT_TITLE_RE.search(t))


def build_book_cards(book):
    cards = []
    bid = book["id"]
    grp = book.get("group", "")
    cat = book.get("category", "")
    btitle = book.get("title", "")
    ci = 0
    for chap in book.get("chapters", []):
        ctitle = chap.get("title", "").strip()
        if is_front_title(ctitle):          # 整章是前言/序/目录等 -> 跳过
            continue
        secs = chap.get("sections") or [{"title": "", "paras": chap.get("paras", [])}]
        si = 0
        for sec in secs:
            stitle = (sec.get("title", "") or "").strip()
            if is_front_title(stitle):       # 节级废信息 -> 跳过
                continue
            raw = [p for p in sec.get("paras", []) if p and p.strip()]
            paras = [p for p in raw if not PARA_SKIP_RE.search(p)]  # 剔版权/出版行
            if not paras:
                continue
            # 剔除明显乱码卡（几乎不含汉字，属扫描 OCR 损坏）
            alltext = "".join(paras)
            zh = sum(1 for ch in alltext if '\u4e00' <= ch <= '\u9fff')
            if zh == 0 and alltext.strip():
                continue
            name = strip_num(stitle) or strip_num(ctitle)
            is_mn = bool(MNEMONIC_TITLE.search(stitle))
            ctype = "mnemonic" if is_mn else "knowledge"
            front = (name or ctitle or btitle) + (" · 歌诀" if is_mn else "")
            tags = [grp] if grp else []
            if is_mn:
                tags.append("歌诀")
            cards.append({
                "id": f"card_{bid}_{ci}_{si}",
                "bookId": bid,
                "bookTitle": btitle,
                "group": grp,
                "category": cat,
                "chapterTitle": ctitle,
                "sectionTitle": stitle,
                "name": name,
                "type": ctype,
                "front": front,
                "back": "\n".join(paras),
                "tags": tags,
                "level1": grp,
                "level2": btitle,
                "level3": ctitle,
            })
            si += 1
        ci += 1
    return cards


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", default="")
    args = ap.parse_args()
    man = json.load(open(MANIFEST, encoding="utf-8"))
    if args.group:
        man = [b for b in man if b.get("group") == args.group]
    os.makedirs(CARDS_DIR, exist_ok=True)
    all_cards = []
    stat = {}
    for meta in man:
        bid = meta["id"]
        path = os.path.join(BOOKS_DIR, bid + ".json")
        if not os.path.exists(path):
            print("SKIP(no file):", bid)
            continue
        book = json.load(open(path, encoding="utf-8"))
        cards = build_book_cards(book)
        json.dump(cards, open(os.path.join(CARDS_DIR, bid + ".cards.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        all_cards.extend(cards)
        stat[bid] = len(cards)
    json.dump(all_cards, open(ALL_CARDS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    total_k = sum(1 for c in all_cards if c["type"] == "knowledge")
    total_m = sum(1 for c in all_cards if c["type"] == "mnemonic")
    print(f"书本数: {len(stat)}  卡片总数: {len(all_cards)}  (知识点 {total_k} / 歌诀 {total_m})")


if __name__ == "__main__":
    main()
