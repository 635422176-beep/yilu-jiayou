#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档导入器：将 PDF / Word(.docx) / TXT / MD 原文件切分为「书 → 章 → 节 → 段落」，
输出符合 content.js 数据模型的 JSON，并入 content.json（App 构建时内置）。

用法：
  python scripts/import_docs.py --file 中医基础.pdf --title "中医基础理论" --category "中医"
  python scripts/import_docs.py --file book.docx --file notes.txt --out content.json

章节识别（自动）：
  - Markdown：# 书名 / ## 第一章 / ### 小节
  - 中文：第X章 / 一、 / 1.  / 第一节
  - 英文：Chapter 1 / 1.

依赖（按需安装）：
  pip install pymupdf python-docx
TXT/MD 无需依赖。
"""
import argparse
import json
import os
import re
import sys

# ---------- 文本抽取 ----------
def extract_text(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".txt", ".md", ".text"):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    if ext == ".pdf":
        try:
            import fitz  # PyMuPDF
        except ImportError:
            sys.exit("PDF 需要 PyMuPDF：pip install pymupdf")
        doc = fitz.open(path)
        out = []
        for page in doc:
            out.append(page.get_text())
        return "\n".join(out)
    if ext == ".docx":
        try:
            import docx
        except ImportError:
            sys.exit("DOCX 需要 python-docx：pip install python-docx")
        d = docx.Document(path)
        out = []
        for p in d.paragraphs:
            if p.text.strip():
                out.append(p.text)
        # 也捞表格文本
        for tbl in d.tables:
            for row in tbl.rows:
                out.append("  ".join(c.text for c in row.cells))
        return "\n".join(out)
    sys.exit(f"不支持的文件类型：{ext}")

# ---------- 章节切分 ----------
RE_MD = re.compile(r"^(#{1,6})\s+(.*)$")
RE_CHAP_CN = re.compile(r"^第\s*[0-9零一二三四五六七八九十百]+\s*[章回节篇卷]")
RE_CHAP_CN2 = re.compile(r"^[一二三四五六七八九十]+、")
RE_CHAP_NUM = re.compile(r"^[0-9]+[.、]")
RE_CHAP_EN = re.compile(r"^(chapter|part)\s+[0-9]", re.I)

def parse_book(title_arg, category, text):
    lines = [l.rstrip() for l in text.split("\n")]
    title = (title_arg or "").strip() or "未命名书稿"
    chapters = []
    cur_chap = None
    cur_sec = None

    def new_chap(t):
        return {"id": "c_" + str(abs(hash(t + str(len(chapters))))), "title": t, "paras": [], "sections": []}

    def new_sec(t):
        return {"title": t, "paras": []}

    for line in lines:
        s = line.strip()
        if not s:
            continue
        m = RE_MD.match(s)
        if m:
            lvl = len(m.group(1))
            t = m.group(2).strip()
            if lvl == 1:
                if not title_arg.strip():
                    title = t
                continue
            if lvl == 2:
                cur_chap = new_chap(t); chapters.append(cur_chap); cur_sec = None; continue
            if lvl >= 3:
                if not cur_chap:
                    cur_chap = new_chap(title); chapters.append(cur_chap)
                cur_sec = new_sec(t); cur_chap["sections"].append(cur_sec); continue
        if RE_CHAP_CN.match(s) or RE_CHAP_CN2.match(s) or RE_CHAP_NUM.match(s) or RE_CHAP_EN.match(s):
            cur_chap = new_chap(s); chapters.append(cur_chap); cur_sec = None; continue
        if not cur_chap:
            cur_chap = new_chap(title); chapters.append(cur_chap)
        (cur_sec or cur_chap)["paras"].append(s)

    # 丢弃空章节
    clean = []
    for c in chapters:
        if c["sections"]:
            c["sections"] = [s for s in c["sections"] if s["paras"]]
        if c["paras"] or c["sections"]:
            clean.append(c)
    if not clean:
        clean = [{"id": "c_0", "title": title, "paras": [l for l in lines if l.strip()], "sections": []}]
    return {"title": title, "category": category or "导入", "chapters": clean, "_user": False}

# ---------- 合并输出 ----------
def merge_into(out_path, book):
    data = {"books": []}
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    # 同名书替换，否则追加
    books = data.get("books", [])
    for i, b in enumerate(books):
        if b.get("title") == book["title"]:
            books[i] = book
            break
    else:
        books.append(book)
    data["books"] = books
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return len(books)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", action="append", required=True, help="输入文件（可多次）")
    ap.add_argument("--title", default="", help="书名（缺省取首行/# 标题）")
    ap.add_argument("--category", default="", help="分类，如 中医/内科")
    ap.add_argument("--out", default="content.json", help="输出 content.json 路径")
    args = ap.parse_args()

    # 多文件合并为一本书，按顺序拼接文本
    merged_text = []
    for fp in args.file:
        if not os.path.exists(fp):
            sys.exit(f"文件不存在：{fp}")
        print(f"[提取] {fp}")
        merged_text.append(extract_text(fp))
    text = "\n".join(merged_text)

    book = parse_book(args.title, args.category, text)
    n = merge_into(args.out, book)
    print(f"[完成] 《{book['title']}》共 {len(book['chapters'])} 章，已写入 {args.out}（当前共 {n} 本）")

if __name__ == "__main__":
    main()
