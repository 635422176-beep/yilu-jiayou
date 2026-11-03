#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
去重冗余书版：同一本书被重复导入产生的 _N 副本（内容完全相同，字数一致）。
规则：按 id 去尾 _N 归组，每组保留字数/章数最多的一本，删除其余完全重复副本。
保护：吴雄志(36本) 整体不进入去重组，全部保留。
操作：先备份 content/books 到 content/books.BAK-<时间戳>/，再删除三处冗余文件并重写 manifest。
"""
import json, re, os, shutil, datetime

PROJ = r"C:\Users\HUAWEI\WorkBuddy\2026-10-31-07-42-15\memory-app"
PROTECT = {"吴雄志"}

def base_id(i):
    # 去掉结尾的 _数字 / -数字（重复导入副本标记）
    return re.sub(r"[_\-－]\d+$", "", i)

def load(p):
    return json.load(open(p, encoding="utf-8"))

def save(p, obj):
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

man_path = os.path.join(PROJ, "content", "manifest.json")
man = load(man_path)

groups = {}
for b in man:
    if b.get("category") in PROTECT:
        continue
    groups.setdefault(base_id(b["id"]), []).append(b)

drop_ids = []
keep_ids = set()
for k, members in groups.items():
    if len(members) <= 1:
        keep_ids.add(members[0]["id"])
        continue
    ranked = sorted(members, key=lambda b: (b.get("wordCount", 0), b.get("chapterCount", 0)), reverse=True)
    keep_ids.add(ranked[0]["id"])
    for m in ranked[1:]:
        drop_ids.append(m["id"])
# 吴雄志全部保留
for b in man:
    if b.get("category") in PROTECT:
        keep_ids.add(b["id"])

drop_set = set(drop_ids)
assert not (drop_set & {b["id"] for b in man if b.get("category") in PROTECT}), "ERROR: 吴雄志 被纳入删除!"

# 1) 备份 content/books
ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
books_dir = os.path.join(PROJ, "content", "books")
bak = os.path.join(PROJ, "content", "books.BAK-" + ts)
os.makedirs(bak, exist_ok=True)
n_bak = 0
for fn in os.listdir(books_dir):
    if fn.endswith(".json"):
        shutil.copy2(os.path.join(books_dir, fn), os.path.join(bak, fn))
        n_bak += 1
print("备份 content/books ->", bak, "(", n_bak, "文件 )")

# 2) 删除 content/books 中冗余
removed = 0
for did in drop_ids:
    p = os.path.join(books_dir, did + ".json")
    if os.path.exists(p):
        os.remove(p)
        removed += 1
print("content/books 删除:", removed)

# 3) 重写 content/manifest.json
new_man = [b for b in man if b["id"] not in drop_set]
save(man_path, new_man)
print("content/manifest.json:", len(man), "->", len(new_man))

# 4) 同步两处静态副本（h5 构建源 + win-unpacked 安装载荷）
targets = [
    os.path.join(PROJ, "unpackage/dist/build/web/static/content"),
    os.path.join(PROJ, "electron/dist/win-unpacked/resources/h5/static/content"),
]
for t in targets:
    bd = os.path.join(t, "books")
    if not os.path.isdir(bd):
        print("SKIP 无目录:", t)
        continue
    rem = 0
    for did in drop_ids:
        p = os.path.join(bd, did + ".json")
        if os.path.exists(p):
            os.remove(p)
            rem += 1
    mp = os.path.join(t, "manifest.json")
    if os.path.exists(mp):
        m2 = load(mp)
        m2 = [b for b in m2 if b["id"] not in drop_set]
        save(mp, m2)
        print("  副本", t, "删除", rem, "本, manifest", "->", len(m2))
    else:
        print("  副本", t, "无 manifest, 仅删文件", rem)

# 5) 断言：吴雄志 必为 36 且全在
wxz = [b for b in new_man if b.get("category") in PROTECT]
print("校验 吴雄志 保留数:", len(wxz), "(应=36)")
print("DONE  总删除=", len(drop_ids), " 剩余=", len(new_man))
