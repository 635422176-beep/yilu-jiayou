// services/content.js
// 章节化内容层（懒加载版）：
//   - 内置书：清单 manifest.json + 单本 books/<id>.json，运行时按书 fetch，绝不一次载入全部。
//   - 用户导入书：localStorage。
//   - 复习排期 / 书签 / 笔记 / 摘录：localStorage。
//   - 书籍隐藏(删除) 与 分类覆盖(移动文件夹)：localStorage（不改动打包内的只读文件）。
// 阅读按「书 → 章（→ 节）→ 段落」连续呈现，不做任何题目切割。
const BASE = '/static/content/'

let _manifest = null
let _manifestLoading = null

const K_USER = 'reader_user_books'
const K_REV = 'reader_review'
const K_HIDDEN = 'reader_hidden_books'     // 软删除（隐藏）的书 id 列表
const K_CAT_OVR = 'reader_cat_overrides'   // { [bookId]: 新分类 }
const K_EXC = 'reader_excerpts'            // { [bookId]: [ {id,text,ci,si,note,inReview,ts} ] }
const K_EXC_REV = 'reader_excerpt_review'  // { [bookId|exId]: {ease,interval,repetitions,dueDate} }
const K_EDIT = 'reader_text_edits'         // 本地改写覆盖层（绝不改打包原文）：
                                            //   { [bookId]: { [ci]: { [si]: { [pi]: "改写后的文字" } } } }
                                            //   si 用数字；章级段落（无节）统一用 si = -1，与阅读器锚点一致。

/* ---------- 清单 / 单本加载 ---------- */
export function loadManifest() {
  if (_manifest) return Promise.resolve(_manifest)
  if (_manifestLoading) return _manifestLoading
  _manifestLoading = fetch(BASE + 'manifest.json')
    .then(r => { if (!r.ok) throw new Error('清单不存在'); return r.json() })
    .then(m => { _manifest = Array.isArray(m) ? m : []; return _manifest })
    .catch(() => { _manifest = []; return _manifest })
  return _manifestLoading
}
export function getManifest() { return _manifest || [] }

export function loadBook(id) {
  // 用户导入书优先（本地）
  const u = (uni.getStorageSync(K_USER) || []).find(b => b.id === id)
  if (u) return Promise.resolve(u)
  return fetch(BASE + 'books/' + encodeURIComponent(id) + '.json')
    .then(r => { if (!r.ok) throw new Error('book 404 ' + id); return r.json() })
}

/* ---------- 用户导入书 ---------- */
export function getUserBooks() { return uni.getStorageSync(K_USER) || [] }
export function addUserBook(book) {
  const users = getUserBooks()
  users.push(book)
  uni.setStorageSync(K_USER, users)
}
export function removeUserBook(id) {
  const users = getUserBooks().filter(b => b.id !== id)
  uni.setStorageSync(K_USER, users)
}

/* ---------- 书籍隐藏（软删除）/ 恢复 ---------- */
export function getHidden() { return uni.getStorageSync(K_HIDDEN) || [] }
export function isHidden(id) { return getHidden().includes(id) }
export function hideBook(id) {
  const h = getHidden()
  if (!h.includes(id)) { h.push(id); uni.setStorageSync(K_HIDDEN, h) }
}
export function restoreBook(id) {
  uni.setStorageSync(K_HIDDEN, getHidden().filter(x => x !== id))
}

/* ---------- 分类覆盖（移动文件夹） ---------- */
export function getCatOverrides() { return uni.getStorageSync(K_CAT_OVR) || {} }
export function setCatOverride(id, cat) {
  const o = getCatOverrides()
  if (cat && cat.trim()) o[id] = cat.trim()
  else delete o[id]
  uni.setStorageSync(K_CAT_OVR, o)
}
export function getCatOf(b) {
  const o = getCatOverrides()
  return (b && b.id && o[b.id]) || (b && b.category) || '未分类'
}

/* ---------- 合并元数据（内置清单 + 用户书） ---------- */
// opts.includeHidden=true 时连被隐藏的书也返回（用于管理页恢复）。
export function getAllBookMeta(opts = {}) {
  const inc = !!opts.includeHidden
  let all = [...getManifest(), ...getUserBooks()]
  if (!inc) all = all.filter(b => !isHidden(b.id))
  return all
}
export function getCategories() {
  const map = {}
  getAllBookMeta().forEach(b => {
    const cat = (getCatOf(b) || '').trim() || '未分类'
    ;(map[cat] = map[cat] || []).push(b)
  })
  return map
}
export function searchBooks(q) {
  const s = (q || '').trim().toLowerCase()
  const all = getAllBookMeta()
  if (!s) return all
  return all.filter(b =>
    (b.title || '').toLowerCase().includes(s) ||
    (getCatOf(b) || '').toLowerCase().includes(s)
  )
}
export function getBookMeta(id) {
  return getAllBookMeta({ includeHidden: true }).find(b => b.id === id) || null
}

/* ---------- 章节稳定 id（修内置书 chapters 无 id 导致复习失效） ---------- */
export function chapterKey(book, ci) {
  const c = book && book.chapters && book.chapters[ci]
  return (c && c.id) ? c.id : (book.id + '#' + ci)
}

/* ---------- 章节复习（章节级 SM-2，排期存于本地） ---------- */
export function getReviewMap() { return uni.getStorageSync(K_REV) || {} }
export function saveReviewMap(m) { uni.setStorageSync(K_REV, m) }
export function isInReview(bookId, chapterKey_) {
  return !!(getReviewMap()[bookId + '|' + chapterKey_])
}
export function addToReview(bookId, chapterKey_) {
  const m = getReviewMap()
  const key = bookId + '|' + chapterKey_
  if (!m[key]) m[key] = { ease: 2.5, interval: 0, repetitions: 0, dueDate: Date.now() }
  saveReviewMap(m)
}
export function removeFromReview(bookId, chapterKey_) {
  const m = getReviewMap()
  delete m[bookId + '|' + chapterKey_]
  saveReviewMap(m)
}
export function setReviewSchedule(bookId, chapterKey_, sched) {
  const m = getReviewMap()
  m[bookId + '|' + chapterKey_] = sched
  saveReviewMap(m)
}

/* ---------- 摘录：选中文字 → 笔记 / 加入背诵 ---------- */
export function getExcerptsAll() { return uni.getStorageSync(K_EXC) || {} }
export function getBookExcerpts(bookId) { return getExcerptsAll()[bookId] || [] }
export function addExcerpt(bookId, ex) {
  const all = getExcerptsAll()
  all[bookId] = all[bookId] || []
  all[bookId].push(ex)
  uni.setStorageSync(K_EXC, all)
  return ex
}
export function updateExcerpt(bookId, exId, patch) {
  const all = getExcerptsAll()
  const list = all[bookId] || []
  const i = list.findIndex(e => e.id === exId)
  if (i >= 0) { list[i] = { ...list[i], ...patch }; uni.setStorageSync(K_EXC, all) }
}
export function removeExcerpt(bookId, exId) {
  const all = getExcerptsAll()
  all[bookId] = (all[bookId] || []).filter(e => e.id !== exId)
  uni.setStorageSync(K_EXC, all)
}

/* ---------- 摘录复习排期 ---------- */
export function getExcReviewMap() { return uni.getStorageSync(K_EXC_REV) || {} }
export function isExcerptInReview(bookId, exId) {
  return !!(getExcReviewMap()[bookId + '|' + exId])
}
export function addExcerptToReview(bookId, exId) {
  const m = getExcReviewMap()
  const k = bookId + '|' + exId
  if (!m[k]) m[k] = { ease: 2.5, interval: 0, repetitions: 0, dueDate: Date.now() }
  uni.setStorageSync(K_EXC_REV, m)
  updateExcerpt(bookId, exId, { inReview: true })
}
export function removeExcerptFromReview(bookId, exId) {
  const m = getExcReviewMap()
  delete m[bookId + '|' + exId]
  uni.setStorageSync(K_EXC_REV, m)
  updateExcerpt(bookId, exId, { inReview: false })
}
export function setExcReviewSchedule(bookId, exId, sched) {
  const m = getExcReviewMap()
  m[bookId + '|' + exId] = sched
  uni.setStorageSync(K_EXC_REV, m)
}

/* ---------- 本地文字改写覆盖层（feature：改原文，不碰打包文件） ---------- */
export function getEditMapAll() { return uni.getStorageSync(K_EDIT) || {} }
export function getBookEdits(bookId) { return getEditMapAll()[bookId] || null }
// 返回某段改写后的文字；无改写返回 null。si=-1 表示章级段落。
export function paraEditAt(bookId, ci, si, pi) {
  const b = getBookEdits(bookId)
  if (!b) return null
  const c = b[ci]; if (!c) return null
  const s = c[si]; if (!s) return null
  const v = s[pi]
  return (v === undefined || v === null) ? null : v
}
// 保存/清除某段改写：text 清空或与原文一致 → 视为还原（删除该项）。
export function setParaEdit(bookId, ci, si, pi, text) {
  const all = getEditMapAll()
  all[bookId] = all[bookId] || {}
  const c = all[bookId][ci] = all[bookId][ci] || {}
  const s = c[si] = c[si] || {}
  const t = (text || '').trim()
  if (!t) delete s[pi]
  else s[pi] = text        // 保留首尾空白由 UI 决定，这里存用户输入
  // 清理空壳，避免无用键堆积
  if (s && Object.keys(s).length === 0) delete c[si]
  if (c && Object.keys(c).length === 0) delete all[bookId][ci]
  if (all[bookId] && Object.keys(all[bookId]).length === 0) delete all[bookId]
  uni.setStorageSync(K_EDIT, all)
}
export function revertParaEdit(bookId, ci, si, pi) { setParaEdit(bookId, ci, si, pi, '') }
export function revertBookEdits(bookId) {
  const all = getEditMapAll()
  delete all[bookId]
  uni.setStorageSync(K_EDIT, all)
}
export function isBookEdited(bookId) { return !!getBookEdits(bookId) }
export function countBookEdits(bookId) {
  const b = getBookEdits(bookId); if (!b) return 0
  let n = 0
  Object.values(b).forEach(c => Object.values(c).forEach(s => { n += Object.keys(s).length }))
  return n
}

/* ---------- 书内搜索：返回命中位置（章/节/段） ---------- */
// em（可选）= 本书改写覆盖层；传入则按"显示出来的文字"检索，且修正无节章节的 si 为 -1（与锚点一致）。
export function searchInBook(book, q, em) {
  const s = (q || '').trim()
  if (!s) return []
  const hits = []
  const chaps = book.chapters || []
  chaps.forEach((chap, ci) => {
    const hasSec = chap.sections && chap.sections.length
    const secs = hasSec ? chap.sections : [{ title: '', paras: chap.paras || [] }]
    secs.forEach((sec, si) => {
      const sidx = hasSec ? si : -1
      ;(sec.paras || []).forEach((p, pi) => {
        const eff = (em && em[ci] && em[ci][sidx] && em[ci][sidx][pi] !== undefined) ? em[ci][sidx][pi] : p
        if (eff && eff.includes(s)) hits.push({ ci, si: sidx, pi, text: eff })
      })
    })
  })
  return hits
}
