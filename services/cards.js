// services/cards.js
// 卡片应用数据层（按书懒加载，适配桌面 / 小程序双端）。
// 资源约定：/static/content/manifest.json（轻量书目）
//          /static/content/cards/<bookId>.cards.json（单书卡片，打开时再读）
import { scheduleNext, isDue } from '../utils/review.js'

const LOCAL_BASE = '/static/content/'
// 小程序端：把 public/static/content 上传到任意静态托管后，将此处改为该 https 地址
// （例如 'https://your-cdn.com/cards/'）。留空字符串则使用本地 /static/content/（桌面端）。
// 小程序端（mp-weixin）走 GitHub Pages 远程卡片，其余（h5 / 桌面）用本地打包的 static。
// UNI_PLATFORM 由 uni-app 在编译期替换为字面量，运行时即确定值。
const IS_MP = (typeof process !== 'undefined' && process.env && process.env.UNI_PLATFORM === 'mp-weixin')
export const CARD_BASE = IS_MP ? 'https://635422176-beep.github.io/yilu-jiayou/static/content/' : ''
const BASE = CARD_BASE || LOCAL_BASE
let _manifest = null
const _bookCache = {}

function req(url) {
  return new Promise((resolve, reject) => {
    uni.request({ url, success: (res) => resolve(res.data), fail: (e) => reject(e) })
  })
}

export async function loadManifest() {
  if (_manifest) return _manifest
  _manifest = await req(BASE + 'manifest.json')
  return _manifest
}

export async function loadBookCards(bookId) {
  if (_bookCache[bookId]) return _bookCache[bookId]
  const r = await req(BASE + 'cards/' + bookId + '.cards.json')
  _bookCache[bookId] = r
  return r
}

// group -> books（不含章节，章节在打开书时再算）
export function buildTree(manifest) {
  const groups = {}
  for (const b of manifest) {
    const g = b.group || '未分类'
    groups[g] = groups[g] || []
    groups[g].push({ id: b.id, title: b.title, category: b.category, chapterCount: b.chapterCount })
  }
  return Object.entries(groups).map(([group, books]) => ({ group, books }))
}

export function chaptersOf(cards) {
  const m = {}
  for (const c of cards) {
    const t = c.chapterTitle || '未分章'
    ;(m[t] = m[t] || []).push(c)
  }
  return Object.entries(m).map(([title, cs]) => ({ title, cards: cs }))
}

export function getDeck(cards, { chapterTitle } = {}) {
  return chapterTitle ? cards.filter(c => c.chapterTitle === chapterTitle) : cards
}

// ---------- SM-2 排期 + 已学索引（按卡片 id 持久化） ----------
const K_SCHED = 'card_schedules'
const K_STUD = 'card_studied'
function readSched() { try { return JSON.parse(uni.getStorageSync(K_SCHED) || '{}') } catch (e) { return {} } }
function writeSched(o) { uni.setStorageSync(K_SCHED, JSON.stringify(o)) }
function readStudied() { try { return JSON.parse(uni.getStorageSync(K_STUD) || '{}') } catch (e) { return {} } }
function writeStudied(o) { uni.setStorageSync(K_STUD, JSON.stringify(o)) }

export function gradeCard(cardId, grade, meta) {
  const all = readSched()
  const next = scheduleNext(all[cardId], grade)
  all[cardId] = { ...next, lastGrade: grade, ts: Date.now() }
  writeSched(all)
  const st = readStudied()
  st[cardId] = { ...meta, id: cardId }
  writeStudied(st)
  return next
}
export function getSchedule(cardId) { return readSched()[cardId] }

// 到期卡片（用于复习页）：返回 {id, bookId, front, chapterTitle, type}
export function dueStudied() {
  const all = readSched()
  const st = readStudied()
  const today = new Date()
  return Object.keys(all)
    .filter(id => isDue(all[id], today))
    .map(id => ({ id, ...st[id] }))
}
export function stats() {
  const all = readSched()
  const due = Object.keys(all).filter(id => isDue(all[id], new Date())).length
  return { learned: Object.keys(all).length, due }
}
export function resetAll() { uni.removeStorageSync(K_SCHED); uni.removeStorageSync(K_STUD) }
