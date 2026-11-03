<template>
  <view class="page">
    <!-- ===================== 阅读视图 ===================== -->
    <block v-if="reading">
      <view class="reader-head">
        <text class="back" @click="goUp">‹ 返回</text>
        <view class="reader-title">
          <text class="rt-book">{{ reading.book.title }}</text>
          <text class="rt-sub">{{ getCatOf(reading.book) }}</text>
        </view>
        <view class="head-tools">
          <text class="ht" @click="openToc">目录</text>
          <text class="ht" @click="toggleSearch">{{ showSearch ? '✕' : '🔍' }}</text>
          <text class="ht" @click="openBookmarks">书签{{ markedCount ? '·' + markedCount : '' }}</text>
          <text class="ht" @click="showSettings = true">Aa</text>
          <text class="ht" @click="openBookOpts">⋯</text>
        </view>
      </view>

      <view v-if="distill" class="distill-bar">精简模式（保留每节首句要点，章节结构不变）</view>

      <view v-if="showSearch" class="bksearch">
        <input class="bksearch-input" :value="bookKw" @input="onBookKw" placeholder="在此书内查找文字…" placeholder-class="ph" />
        <text v-if="bookKw.trim() && bookHits.length" class="bksearch-cnt" @click="openHits">{{ bookHits.length }} 处结果 ›</text>
        <text v-else-if="bookKw.trim()" class="bksearch-cnt">无结果</text>
      </view>

      <scroll-view class="reader-body" scroll-y :scroll-into-view="scrollTarget" scroll-with-animation>
        <view class="note">按章节连续阅读。顶部「目录」按章/节跳转，「🔍」书内查找；选中正文文字可「摘录」记笔记或加入背诵，或点「✎」浮动按钮改写该段（改动仅存本机，原书不变）。章节右侧「复习」加入间隔复习、「☆」书签、「✎」笔记。</view>
        <block v-for="(chap, ci) in reading.book.chapters" :key="chap.id || ci">
          <view :id="'chap-' + ci" class="chap-block">
            <view class="chap-head">
              <text class="chap-title" @click="tocJump(ci)">{{ ci + 1 }}. {{ chap.title }}</text>
              <view class="chap-tools">
                <text class="tool rev" :class="{ on: inReview(ci) }" @click="toggleReview(ci)">复习</text>
                <text class="tool" :class="{ on: isMarked(ci) }" @click="toggleBookmark(ci)">{{ isMarked(ci) ? '★' : '☆' }}</text>
                <text class="tool" :class="{ on: hasNote(ci) }" @click="openNote(ci)">✎{{ hasNote(ci) ? '●' : '' }}</text>
              </view>
            </view>
            <block v-if="chap.sections && chap.sections.length">
              <view v-for="(sec, si) in chap.sections" :key="si" class="sec-block">
                <view :id="'sec-' + ci + '-' + si" v-if="sec.title" class="sec-title" @click="tocJump(ci, si)">{{ sec.title }}</view>
                <view v-for="(item, pi) in displayParas(sec.paras, ci, si)" :key="pi" :id="anchorOf(ci, si, pi)" :class="['para', item.edited ? 'edited' : '']">
                  <text v-for="(seg, gi) in splitHL(item.text)" :key="gi" :class="['body', seg.hl ? 'hl' : '']" :style="bodyStyle">{{ seg.t }}</text>
                </view>
              </view>
            </block>
            <block v-else>
              <view v-for="(item, pi) in displayParas(chap.paras, ci, -1)" :key="pi" :id="anchorOf(ci, -1, pi)" :class="['para', item.edited ? 'edited' : '']">
                <text v-for="(seg, gi) in splitHL(item.text)" :key="gi" :class="['body', seg.hl ? 'hl' : '']" :style="bodyStyle">{{ seg.t }}</text>
              </view>
            </block>
          </view>
        </block>
        <view class="end-space"></view>
      </scroll-view>

      <!-- 常驻浮动按钮：返回 + 改写 + 摘录 -->
      <view class="fab fab-back" @click="goUp">‹</view>
      <view class="fab fab-edit" @click="openEdit">✎</view>
      <view class="fab fab-exc" @click="captureSelection">摘录</view>

      <!-- 目录抽屉 -->
      <view v-if="showToc" class="mask" @click="showToc = false">
        <view class="toc" @click.stop>
          <view class="toc-head">
            <text class="toc-title">目录（{{ reading.book.chapters.length }} 章）</text>
            <text class="toc-close" @click="showToc = false">✕</text>
          </view>
          <scroll-view scroll-y class="toc-body">
            <view v-for="(chap, ci) in reading.book.chapters" :key="ci" class="toc-chap">
              <view class="toc-chap-title" @click="tocJump(ci)">{{ ci + 1 }}. {{ chap.title }}</view>
              <view v-if="chap.sections && chap.sections.length" class="toc-secs">
                <view v-for="(sec, si) in chap.sections" :key="si" class="toc-sec" @click="tocJump(ci, si)">{{ sec.title || ('第 ' + (si + 1) + ' 节') }}</view>
              </view>
            </view>
          </scroll-view>
        </view>
      </view>

      <!-- 书内搜索结果 -->
      <view v-if="showHits" class="mask" @click="showHits = false">
        <view class="sheet hits" @click.stop>
          <view class="sheet-head">
            <text class="sheet-title">查找结果（{{ bookHits.length }} 处）</text>
            <text class="sheet-close" @click="showHits = false">✕</text>
          </view>
          <scroll-view scroll-y class="sheet-body">
            <view v-for="(h, i) in bookHits" :key="i" class="hit-item" @click="jumpHit(i)">
              <text class="hit-pos">{{ h.ci + 1 }}.{{ h.si + 1 }} · {{ snippet(h.text) }}</text>
            </view>
          </scroll-view>
        </view>
      </view>

      <!-- 书签列表面板 -->
      <view v-if="showBookmarks" class="mask" @click="showBookmarks = false">
        <view class="sheet" @click.stop>
          <view class="sheet-head">
            <text class="sheet-title">本书书签</text>
            <text class="sheet-close" @click="showBookmarks = false">✕</text>
          </view>
          <scroll-view scroll-y class="sheet-body">
            <view v-if="!markedChapters.length" class="sheet-empty">还没有书签，点章节右侧 ☆ 即可添加</view>
            <view v-for="m in markedChapters" :key="m.ci" class="sheet-item" @click="jumpTo(m.ci)">
              <text class="si-dot">★</text>
              <text class="si-title">{{ m.title }}</text>
              <text v-if="hasNote(m.ci)" class="si-note">✎</text>
            </view>
          </scroll-view>
        </view>
      </view>

      <!-- 笔记面板 -->
      <view v-if="noteEditing !== null" class="mask" @click="closeNote">
        <view class="sheet" @click.stop>
          <view class="sheet-head">
            <text class="sheet-title">笔记 · {{ reading.book.chapters[noteEditing].title }}</text>
            <text class="sheet-close" @click="closeNote">✕</text>
          </view>
          <textarea class="note-input" :value="noteDraft" @input="onNoteInput"
            placeholder="在此写下心得、疑问或摘录……" maxlength="-1" />
          <view class="sheet-foot">
            <button class="sf-btn ghost" @click="closeNote">取消</button>
            <button class="sf-btn" @click="saveNoteDraft">保存笔记</button>
          </view>
        </view>
      </view>

      <!-- 阅读设置 -->
      <view v-if="showSettings" class="mask" @click="showSettings = false">
        <view class="sheet" @click.stop>
          <view class="sheet-head">
            <text class="sheet-title">阅读设置</text>
            <text class="sheet-close" @click="showSettings = false">✕</text>
          </view>
          <view class="set-row">
            <text class="set-label">字号</text>
            <slider class="set-slider" :value="fontSize" min="24" max="46" step="1" show-value @change="onFont" activeColor="#07c160" />
          </view>
          <view class="set-row">
            <text class="set-label">行距</text>
            <slider class="set-slider" :value="lineHeight" min="1.4" max="2.6" step="0.1" show-value @change="onLine" activeColor="#07c160" />
          </view>
          <view class="set-row switch-row">
            <text class="set-label">蒸馏精简</text>
            <switch :checked="distill" @change="onDistill" color="#07c160" />
          </view>
          <text class="set-tip">精简：离线启发式保留每节首句要点（非 AI 摘要，保留全部章节结构）。</text>
        </view>
      </view>

      <!-- 本书操作菜单（隐藏/删除 + 移动分类） -->
      <view v-if="showBookOpts" class="mask" @click="showBookOpts = false">
        <view class="sheet" @click.stop>
          <view class="sheet-head">
            <text class="sheet-title">本书操作</text>
            <text class="sheet-close" @click="showBookOpts = false">✕</text>
          </view>
          <view class="opt-row">
            <text class="opt-label">移动到分类（文件夹）</text>
          </view>
          <view class="opt-row">
            <input class="opt-input" :value="moveCat" @input="onMoveCat" placeholder="输入新分类名，如：中医/内经" />
            <button class="opt-btn" @click="doMoveCat">确定移动</button>
          </view>
          <view class="opt-row opt-actions">
            <button class="opt-btn danger" v-if="!reading.book._user" @click="doHide">{{ isHidden(reading.book.id) ? '恢复此书' : '隐藏 / 删除此书' }}</button>
            <button class="opt-btn danger" v-else @click="doHide">彻底删除此书</button>
          </view>
          <view class="opt-row opt-actions" v-if="isBookEdited(reading.book.id)">
            <button class="opt-btn" @click="doRevertBook">还原全部改写（{{ countBookEdits(reading.book.id) }} 处）</button>
          </view>
          <text class="set-tip">内置书为只读打包文件，删除=从书架隐藏（可恢复）；导入书为彻底删除。你对正文的改写只存在本机覆盖层，原书文件不变，可随时一键还原。</text>
        </view>
      </view>

      <!-- 摘录动作面板 -->
      <view v-if="showExcerpt" class="mask" @click="showExcerpt = false">
        <view class="sheet" @click.stop>
          <view class="sheet-head">
            <text class="sheet-title">摘录选中文字</text>
            <text class="sheet-close" @click="showExcerpt = false">✕</text>
          </view>
          <view class="exc-text">{{ excerptDraft }}</view>
          <textarea class="note-input" :value="excNote" @input="onExcNote"
            placeholder="可写备注（选填）……" maxlength="-1" />
          <view class="sheet-foot">
            <button class="sf-btn ghost" @click="saveExcerpt(false)">仅记笔记</button>
            <button class="sf-btn" @click="saveExcerpt(true)">加入背诵</button>
          </view>
        </view>
      </view>

      <!-- 改写段落面板（仅本地覆盖，不动原书） -->
      <view v-if="showEdit" class="mask" @click="showEdit = false">
        <view class="sheet" @click.stop>
          <view class="sheet-head">
            <text class="sheet-title">改写段落（仅存本机，原书不动）</text>
            <text class="sheet-close" @click="showEdit = false">✕</text>
          </view>
          <textarea class="note-input edit-area" :value="editDraft" @input="onEditInput"
            placeholder="在此改写这段文字，纠错或重写均可……" maxlength="-1" />
          <text class="set-tip">改动只存在本机覆盖层，原书文件保持原样；清空或改回原文即还原。</text>
          <view class="sheet-foot">
            <button class="sf-btn ghost" @click="revertEdit">还原此段</button>
            <button class="sf-btn" @click="saveEdit">保存改写</button>
          </view>
        </view>
      </view>
    </block>

    <!-- ===================== 目录导航 ===================== -->
    <block v-else>
      <view class="nav-head">
        <text class="nav-title">{{ currentTitle }}</text>
        <text class="nav-up" v-if="showUp" @click="goUp">‹ 返回上级</text>
      </view>
      <view class="search-bar">
        <input class="search-input" :value="kw" @input="onKw" placeholder="搜索书名 / 分类" placeholder-class="ph" />
      </view>
      <scroll-view class="nav-body" scroll-y>
        <view v-if="!stack.length" class="tip">选择分类，再点书名即可连续阅读原著。共 {{ totalBooks }} 本。</view>
        <view v-for="item in currentList" :key="item.key" class="nav-item" @click="enter(item)">
          <text class="ni-name">{{ item.name }}</text>
          <text class="ni-cnt">{{ item.count }}</text>
          <text class="arrow">›</text>
        </view>
        <view v-if="!currentList.length && stack.length" class="tip">暂无内容。去「导入」页录入书稿，或把原文件交给我处理。</view>
      </scroll-view>
      <view v-if="showUp" class="fab fab-back" @click="goUp">‹</view>
    </block>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow, onBackPress, onHide } from '@dcloudio/uni-app'
import {
  loadManifest, getManifest, loadBook, getCategories, searchBooks, getCatOf,
  isInReview, addToReview, removeFromReview, chapterKey, searchInBook,
  isHidden, hideBook, restoreBook, setCatOverride, removeUserBook,
  addExcerpt, addExcerptToReview,
  getBookEdits, paraEditAt, setParaEdit, revertBookEdits, isBookEdited, countBookEdits
} from '../../services/content.js'

const stack = ref([])
const reading = ref(null)
const active = ref(false)
const kw = ref('')
const loading = ref(false)

const FONT_KEY = 'reader_font'
const MARK_KEY = 'reader_bookmarks'
const NOTE_KEY = 'reader_notes'

const fontSize = ref(31)
const lineHeight = ref(1.85)
const distill = ref(false)
const showSettings = ref(false)
const showBookmarks = ref(false)
const noteEditing = ref(null)
const noteDraft = ref('')
const scrollTarget = ref('')

/* 新增强化 */
const showToc = ref(false)
const showSearch = ref(false)
const bookKw = ref('')
const bookHits = ref([])
const showHits = ref(false)
const showBookOpts = ref(false)
const moveCat = ref('')
const showExcerpt = ref(false)
const excerptDraft = ref('')
const excNote = ref('')
const excerptCi = ref(-1)

/* 本地改写覆盖层（feature：改原文） */
const bookEdits = ref({})        // 当前书的改写层（响应式，保存后重赋值触发重渲染）
const showEdit = ref(false)
const editDraft = ref('')
const editTarget = ref(null)     // { ci, si, pi }
const editOriginal = ref('')

const bodyStyle = computed(() => ({
  fontSize: fontSize.value + 'rpx',
  lineHeight: String(lineHeight.value),
  textAlign: 'justify'
}))

const totalBooks = computed(() => getManifest().length + (uni.getStorageSync('reader_user_books') || []).length)

/* ---------- 字号 / 书签 / 笔记 ---------- */
function loadFont() {
  const f = uni.getStorageSync(FONT_KEY)
  if (f) {
    if (f.size) fontSize.value = f.size
    if (f.lh) lineHeight.value = f.lh
    if (typeof f.distill === 'boolean') distill.value = f.distill
  }
}
function saveFont() { uni.setStorageSync(FONT_KEY, { size: fontSize.value, lh: lineHeight.value, distill: distill.value }) }
function onFont(e) { fontSize.value = e.detail.value; saveFont() }
function onLine(e) { lineHeight.value = e.detail.value; saveFont() }
function onDistill(e) { distill.value = e.detail.value; saveFont() }
function onKw(e) { kw.value = e.detail.value }
function onBookKw(e) { bookKw.value = e.detail.value; runBookSearch() }

function markMap() { return uni.getStorageSync(MARK_KEY) || {} }
function noteMap() { return uni.getStorageSync(NOTE_KEY) || {} }
function bkKey() { return reading.value && reading.value.book.id }
function isMarked(ci) { const m = markMap()[bkKey()]; return !!(m && m[ci]) }
function hasNote(ci) { const n = noteMap()[bkKey()]; return !!(n && n[ci]) }
function toggleBookmark(ci) {
  const all = markMap(); const bk = bkKey()
  all[bk] = all[bk] || {}
  if (all[bk][ci]) delete all[bk][ci]; else all[bk][ci] = true
  uni.setStorageSync(MARK_KEY, all)
}
function openBookmarks() {
  if (!markedChapters.value.length) uni.showToast({ title: '暂无书签', icon: 'none' })
  showBookmarks.value = true
}
const markedChapters = computed(() => {
  if (!reading.value) return []
  const m = markMap()[bkKey()] || {}
  return reading.value.book.chapters
    .map((c, ci) => ({ ci, title: c.title }))
    .filter(x => m[x.ci])
})
const markedCount = computed(() => markedChapters.value.length)
function jumpTo(ci) {
  scrollTarget.value = ''
  setTimeout(() => { scrollTarget.value = 'chap-' + ci }, 30)
  showBookmarks.value = false
}
function openNote(ci) {
  noteEditing.value = ci
  noteDraft.value = (noteMap()[bkKey()] && noteMap()[bkKey()][ci]) || ''
}
function onNoteInput(e) { noteDraft.value = e.detail.value }
function closeNote() { noteEditing.value = null; noteDraft.value = '' }
function saveNoteDraft() {
  const all = noteMap(); const bk = bkKey()
  all[bk] = all[bk] || {}
  const v = (noteDraft.value || '').trim()
  if (v) all[bk][noteEditing.value] = v; else delete all[bk][noteEditing.value]
  uni.setStorageSync(NOTE_KEY, all)
  closeNote()
  uni.showToast({ title: '已保存', icon: 'none' })
}

/* 章节复习入列（用 chapterKey 修复内置书无 id 问题） */
function inReview(ci) { return reading.value && isInReview(reading.value.book.id, chapterKey(reading.value.book, ci)) }
function toggleReview(ci) {
  const bk = reading.value.book
  const key = chapterKey(bk, ci)
  if (isInReview(bk.id, key)) { removeFromReview(bk.id, key); uni.showToast({ title: '已移出复习', icon: 'none' }) }
  else { addToReview(bk.id, key); uni.showToast({ title: '已加入复习', icon: 'success' }) }
}

/* 蒸馏 */
function condense(t) {
  if (!t) return ''
  const m = t.match(/^[\s\S]{0,140}?[。！？!?；;]/)
  return m ? m[0] : t
}
// 读取当前书改写层（响应式）：返回改写文字或 null
function paraEditEffective(ci, si, pi) {
  const em = bookEdits.value
  if (!em) return null
  const c = em[ci]; if (!c) return null
  const s = c[si]; if (!s) return null
  const v = s[pi]
  return (v === undefined || v === null) ? null : v
}
function displayParas(paras, ci, si) {
  if (!paras) return []
  const bk = bkKey()
  return paras.map((p, pi) => {
    let text = p
    const e = (bk != null) ? paraEditEffective(ci, si, pi) : null
    if (e !== null) text = e
    if (distill.value) text = condense(text)
    return { text, edited: e !== null, pi, ci, si }
  })
}

/* ---------- 目录 / 三级锚点（feature 5） ---------- */
function anchorOf(ci, si, pi) { return 'p-' + ci + '-' + (si < 0 ? 'x' : si) + '-' + pi }
function tocJump(ci, si) {
  showToc.value = false
  scrollTarget.value = ''
  setTimeout(() => {
    scrollTarget.value = (si === undefined || si === null) ? ('chap-' + ci) : ('sec-' + ci + '-' + si)
  }, 30)
}

/* ---------- 书内搜索（feature 3） ---------- */
function runBookSearch() {
  if (!reading.value) { bookHits.value = []; return }
  bookHits.value = searchInBook(reading.value.book, bookKw.value, bookEdits.value)
}
function toggleSearch() {
  showSearch.value = !showSearch.value
  if (!showSearch.value) { bookKw.value = ''; bookHits.value = []; showHits.value = false }
}
function openHits() { if (bookHits.value.length) showHits.value = true }
function snippet(t) { return (t || '').replace(/\s+/g, ' ').slice(0, 40) + ((t || '').length > 40 ? '…' : '') }
function jumpHit(i) {
  const h = bookHits.value[i]; if (!h) return
  showHits.value = false
  scrollTarget.value = ''
  setTimeout(() => { scrollTarget.value = anchorOf(h.ci, h.si, h.pi) }, 30)
}
function splitHL(text) {
  const k = (showSearch.value ? bookKw.value : '').trim()
  if (!k || !text.includes(k)) return [{ t: text, hl: false }]
  const segs = []; let i = 0
  while (true) {
    const idx = text.indexOf(k, i)
    if (idx < 0) { segs.push({ t: text.slice(i), hl: false }); break }
    if (idx > i) segs.push({ t: text.slice(i, idx), hl: false })
    segs.push({ t: k, hl: true })
    i = idx + k.length
  }
  return segs
}

/* ---------- 选中文字 → 摘录（feature 4） ---------- */
function captureSelection() {
  let txt = ''
  try { if (typeof window !== 'undefined' && window.getSelection) txt = window.getSelection().toString() } catch (e) {}
  txt = (txt || '').trim()
  if (!txt) { uni.showToast({ title: '请先在正文里用鼠标选中一段文字', icon: 'none' }); return }
  excerptDraft.value = txt.slice(0, 800)
  // 反查所属章节以提供上下文
  const hit = searchInBook(reading.value.book, txt.slice(0, 30), bookEdits.value)[0]
  excerptCi.value = hit ? hit.ci : -1
  excNote.value = ''
  showExcerpt.value = true
}
function onExcNote(e) { excNote.value = e.detail.value }
function saveExcerpt(toReview) {
  const book = reading.value.book
  const ex = {
    id: 'e_' + Date.now(),
    text: excerptDraft.value,
    ci: excerptCi.value,
    si: -1,
    note: (excNote.value || '').trim(),
    inReview: toReview,
    ts: Date.now()
  }
  addExcerpt(book.id, ex)
  if (toReview) addExcerptToReview(book.id, ex.id)
  showExcerpt.value = false
  uni.showToast({ title: toReview ? '已加入背诵' : '已记笔记', icon: 'success' })
}

/* ---------- 改写段落（feature：本地覆盖层改原文） ---------- */
function reloadEdits() { bookEdits.value = getBookEdits(bkKey()) || {} }
// 从当前选区反查其所属段落的 (ci,si,pi)：向上找带 p- 锚点的 .para 祖先
function locateParaFromSelection() {
  try {
    const sel = (typeof window !== 'undefined' && window.getSelection) ? window.getSelection() : null
    if (!sel || !sel.anchorNode) return null
    let node = sel.anchorNode
    if (node.nodeType === 3) node = node.parentNode   // 文本节点 → 元素
    while (node && node !== document.body) {
      const id = node.id || (node.getAttribute && node.getAttribute('id')) || ''
      if (id && id.indexOf('p-') === 0) {
        const m = id.slice(2).split('-')
        return { ci: +m[0], si: m[1] === 'x' ? -1 : +m[1], pi: +m[2] }
      }
      node = node.parentNode
    }
  } catch (e) {}
  return null
}
// 直接按坐标打开改写面板（已改写段落可点此编辑/还原）
function openEditAt(ci, si, pi) {
  const book = reading.value.book
  const secs = book.chapters[ci].sections
  const paraArr = (secs && secs.length) ? secs[si].paras : book.chapters[ci].paras
  const original = paraArr[pi] || ''
  editOriginal.value = original
  editTarget.value = { ci, si, pi }
  const cur = paraEditEffective(ci, si, pi)
  editDraft.value = cur !== null ? cur : original
  showEdit.value = true
}
// FAB 入口：先选中正文中某段文字，再点 ✎
function openEdit() {
  const loc = locateParaFromSelection()
  if (!loc) { uni.showToast({ title: '请先在正文里用鼠标选中要改写的段落', icon: 'none' }); return }
  openEditAt(loc.ci, loc.si, loc.pi)
}
function onEditInput(e) { editDraft.value = e.detail.value }
function saveEdit() {
  const t = (editDraft.value || '').trim()
  const { ci, si, pi } = editTarget.value
  const isRevert = (t === editOriginal.value.trim())
  setParaEdit(reading.value.book.id, ci, si, pi, isRevert ? '' : t)
  reloadEdits()
  showEdit.value = false
  uni.showToast({ title: isRevert ? '已还原此段' : '已改写', icon: 'none' })
}
function revertEdit() {
  const { ci, si, pi } = editTarget.value
  setParaEdit(reading.value.book.id, ci, si, pi, '')
  reloadEdits()
  showEdit.value = false
  uni.showToast({ title: '已还原此段', icon: 'none' })
}
function doRevertBook() {
  revertBookEdits(reading.value.book.id)
  reloadEdits()
  showBookOpts.value = false
  uni.showToast({ title: '已还原全部改写', icon: 'none' })
}

/* ---------- 本书操作：隐藏/删除 + 移动分类（feature 1） ---------- */
function openBookOpts() {
  moveCat.value = ''
  showBookOpts.value = true
}
function onMoveCat(e) { moveCat.value = e.detail.value }
function doMoveCat() {
  const v = (moveCat.value || '').trim()
  if (!v) { uni.showToast({ title: '请输入分类名', icon: 'none' }); return }
  setCatOverride(reading.value.book.id, v)
  showBookOpts.value = false
  uni.showToast({ title: '已移动到「' + v + '」', icon: 'none' })
}
function doHide() {
  const book = reading.value.book
  if (book._user) {
    removeUserBook(book.id)
    uni.showToast({ title: '已彻底删除', icon: 'none' })
  } else if (isHidden(book.id)) {
    restoreBook(book.id)
    uni.showToast({ title: '已恢复', icon: 'none' })
  } else {
    hideBook(book.id)
    uni.showToast({ title: '已从书架隐藏', icon: 'none' })
  }
  showBookOpts.value = false
  goUp()
}

/* ---------- 导航 ---------- */
const currentList = computed(() => {
  if (!stack.value.length) {
    if (kw.value.trim()) {
      return searchBooks(kw.value).map(b => ({
        key: 'b:' + b.id, name: b.title, count: (b.chapterCount || (b.chapters ? b.chapters.length : 0)) + ' 章',
        node: b, level: 'book'
      }))
    }
    const cats = getCategories()
    return Object.keys(cats).map(c => ({
      key: 'cat:' + c, name: c, count: cats[c].length + ' 本', node: { name: c, books: cats[c] }, level: 'cat'
    }))
  }
  const top = stack.value[stack.value.length - 1]
  if (top.level === 'cat') {
    return top.node.books.map(b => ({
      key: 'b:' + b.id, name: b.title, count: (b.chapterCount || (b.chapters ? b.chapters.length : 0)) + ' 章',
      node: b, level: 'book'
    }))
  }
  return []
})
const currentTitle = computed(() => {
  if (!stack.value.length) return '选择分类'
  return stack.value[stack.value.length - 1].node.name
})
const showUp = computed(() => stack.value.length > 0 || !!reading.value)

async function enter(item) {
  if (item.level === 'cat') { stack.value.push({ level: 'cat', node: item.node }); reading.value = null }
  else if (item.level === 'book') await openBook(item.node)
}
async function openBook(meta) {
  loading.value = true
  try {
    const book = await loadBook(meta.id)
    reading.value = { book }
    bookEdits.value = getBookEdits(book.id) || {}
    scrollTarget.value = ''
    bookKw.value = ''; bookHits.value = []; showSearch.value = false; showHits.value = false
  } catch (e) {
    uni.showToast({ title: '该书加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}
function goUp() {
  if (showSettings.value) { showSettings.value = false; return }
  if (showBookmarks.value) { showBookmarks.value = false; return }
  if (noteEditing.value !== null) { closeNote(); return }
  if (showExcerpt.value) { showExcerpt.value = false; return }
  if (showEdit.value) { showEdit.value = false; return }
  if (showBookOpts.value) { showBookOpts.value = false; return }
  if (showHits.value) { showHits.value = false; return }
  if (showToc.value) { showToc.value = false; return }
  if (reading.value) { reading.value = null; return }
  if (stack.value.length) stack.value.pop()
}

/* ---------- 快捷键 ---------- */
function onKey(e) {
  if (!active.value) return
  if (e.key === 'Escape' || e.key === 'Backspace') {
    if (showSettings.value || showBookmarks.value || noteEditing.value !== null || showExcerpt.value || showEdit.value || showBookOpts.value || showHits.value || showToc.value) { e.preventDefault(); goUp(); return }
    if (reading.value || stack.value.length) { e.preventDefault(); goUp() }
  }
}
onBackPress(() => {
  if (showSettings.value) { showSettings.value = false; return true }
  if (showBookmarks.value) { showBookmarks.value = false; return true }
  if (noteEditing.value !== null) { closeNote(); return true }
  if (showExcerpt.value) { showExcerpt.value = false; return true }
  if (showEdit.value) { showEdit.value = false; return true }
  if (showBookOpts.value) { showBookOpts.value = false; return true }
  if (showHits.value) { showHits.value = false; return true }
  if (showToc.value) { showToc.value = false; return true }
  if (reading.value || stack.value.length) { goUp(); return true }
  return false
})
onHide(() => { active.value = false })
onMounted(() => {
  if (typeof window !== 'undefined') window.addEventListener('keydown', onKey)
})

onShow(async () => {
  active.value = true
  reading.value = null
  stack.value = []
  loadFont()
  await loadManifest()
})
</script>

<style scoped>
.page { height: 100vh; display: flex; flex-direction: column; box-sizing: border-box; }

.nav-head { display: flex; align-items: center; padding: 24rpx 32rpx 8rpx; background: #fff; }
.nav-title { font-size: 34rpx; font-weight: 700; color: #323233; flex: 1; }
.nav-up { font-size: 28rpx; color: #1989fa; }
.search-bar { padding: 8rpx 24rpx 16rpx; background: #fff; }
.search-input { background: #f2f3f5; border-radius: 999rpx; padding: 18rpx 28rpx; font-size: 28rpx; color: #323233; }
.ph { color: #c8c9cc; }
.nav-body { flex: 1; padding: 8rpx 24rpx 60rpx; box-sizing: border-box; }
.tip { padding: 24rpx 8rpx; color: #969799; font-size: 24rpx; line-height: 1.6; }
.nav-item { display: flex; align-items: center; background: #fff; border-radius: 16rpx; padding: 30rpx 32rpx; margin-top: 16rpx; }
.ni-name { font-size: 32rpx; font-weight: 600; color: #323233; flex: 1; }
.ni-cnt { font-size: 24rpx; color: #969799; margin-right: 16rpx; }
.arrow { color: #c8c9cc; font-size: 34rpx; }

.reader-head { display: flex; align-items: center; padding: 20rpx 24rpx; background: #fff; border-bottom: 1rpx solid #f2f3f5; }
.back { font-size: 28rpx; color: #1989fa; width: 110rpx; flex-shrink: 0; }
.reader-title { flex: 1; display: flex; flex-direction: column; align-items: center; min-width: 0; }
.rt-book { font-size: 30rpx; font-weight: 700; color: #323233; max-width: 100%; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.rt-sub { font-size: 22rpx; color: #969799; margin-top: 4rpx; }
.head-tools { display: flex; flex-shrink: 0; }
.ht { font-size: 26rpx; color: #1989fa; margin-left: 18rpx; }
.distill-bar { background: #e8f8ef; color: #07c160; font-size: 22rpx; text-align: center; padding: 10rpx 0; }
.bksearch { display: flex; align-items: center; padding: 12rpx 24rpx; background: #f7f8fa; border-bottom: 1rpx solid #f2f3f5; }
.bksearch-input { flex: 1; background: #fff; border-radius: 999rpx; padding: 14rpx 24rpx; font-size: 26rpx; color: #323233; }
.bksearch-cnt { font-size: 24rpx; color: #1989fa; margin-left: 16rpx; flex-shrink: 0; }
.reader-body { flex: 1; padding: 24rpx 36rpx 40rpx; box-sizing: border-box; }
.note { font-size: 22rpx; color: #b0b3b8; line-height: 1.5; margin-bottom: 24rpx; }
.chap-block { padding-bottom: 8rpx; }
.chap-head { display: flex; align-items: center; margin: 40rpx 0 16rpx; padding-left: 18rpx; border-left: 8rpx solid #07c160; }
.chap-title { font-size: 34rpx; font-weight: 700; color: #07c160; line-height: 1.4; flex: 1; }
.chap-tools { display: flex; }
.tool { font-size: 26rpx; color: #c8c9cc; margin-left: 18rpx; }
.tool.on { color: #ffb300; }
.tool.rev { font-size: 22rpx; border: 1rpx solid #c8c9cc; border-radius: 8rpx; padding: 2rpx 10rpx; }
.tool.rev.on { color: #07c160; border-color: #07c160; }
.sec-block { margin-top: 8rpx; }
.sec-title { display: block; font-size: 30rpx; font-weight: 600; color: #323233; margin: 20rpx 0 8rpx; }
.para { padding: 12rpx 0; }
.para.edited { border-left: 6rpx solid #ffb300; background: #fffaf0; padding-left: 16rpx; }
.body { color: #323233; }
.body.hl { background: #fff3a0; color: #d9480f; border-radius: 4rpx; }
.end-space { height: 40rpx; }

/* 浮动按钮 */
.fab { position: fixed; z-index: 60; width: 88rpx; height: 88rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 6rpx 20rpx rgba(0,0,0,0.18); font-weight: 700; }
.fab-back { left: 28rpx; bottom: 48rpx; background: #1989fa; color: #fff; font-size: 44rpx; }
.fab-edit { right: 28rpx; bottom: 150rpx; background: #ffb300; color: #fff; font-size: 40rpx; }
.fab-exc { right: 28rpx; bottom: 48rpx; background: #07c160; color: #fff; font-size: 28rpx; }

/* 目录抽屉 */
.mask { position: fixed; left: 0; top: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); z-index: 50; display: flex; }
.toc { width: 78%; height: 100%; background: #fff; display: flex; flex-direction: column; }
.toc-head { display: flex; align-items: center; justify-content: space-between; padding: 28rpx 32rpx; border-bottom: 1rpx solid #f2f3f5; }
.toc-title { font-size: 32rpx; font-weight: 700; color: #323233; }
.toc-close { font-size: 32rpx; color: #969799; padding: 0 8rpx; }
.toc-body { flex: 1; padding: 12rpx 20rpx 40rpx; box-sizing: border-box; }
.toc-chap { padding: 8rpx 0; }
.toc-chap-title { font-size: 30rpx; font-weight: 600; color: #323233; padding: 18rpx 12rpx; background: #f7f8fa; border-radius: 12rpx; }
.toc-secs { padding-left: 24rpx; }
.toc-sec { font-size: 27rpx; color: #646566; padding: 14rpx 12rpx; border-bottom: 1rpx solid #f7f8fa; }
.hits .sheet-body { max-height: 60vh; }
.hit-item { padding: 22rpx 8rpx; border-bottom: 1rpx solid #f2f3f5; }
.hit-pos { font-size: 27rpx; color: #323233; line-height: 1.5; }

/* 通用 sheet */
.sheet { width: 100%; background: #fff; border-radius: 28rpx 28rpx 0 0; padding: 28rpx 32rpx calc(28rpx + env(safe-area-inset-bottom)); box-sizing: border-box; max-height: 80vh; display: flex; flex-direction: column; }
.sheet-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16rpx; }
.sheet-title { font-size: 32rpx; font-weight: 700; color: #323233; }
.sheet-close { font-size: 32rpx; color: #969799; padding: 0 8rpx; }
.sheet-body { flex: 1; max-height: 50vh; }
.sheet-empty { padding: 40rpx 8rpx; color: #969799; font-size: 26rpx; text-align: center; }
.sheet-item { display: flex; align-items: center; padding: 26rpx 8rpx; border-bottom: 1rpx solid #f2f3f5; }
.si-dot { color: #ffb300; font-size: 28rpx; margin-right: 16rpx; }
.si-title { font-size: 30rpx; color: #323233; flex: 1; }
.si-note { color: #1989fa; font-size: 26rpx; }
.note-input { width: 100%; height: 220rpx; background: #f7f8fa; border-radius: 16rpx; padding: 24rpx; box-sizing: border-box; font-size: 30rpx; color: #323233; margin: 8rpx 0 16rpx; }
.sheet-foot { display: flex; gap: 20rpx; }
.sf-btn { flex: 1; background: #07c160; color: #fff; border-radius: 999rpx; font-size: 30rpx; }
.sf-btn.ghost { background: #f2f3f5; color: #323233; }
.set-row { display: flex; align-items: center; padding: 16rpx 0; }
.set-label { font-size: 30rpx; color: #323233; width: 160rpx; flex-shrink: 0; }
.set-slider { flex: 1; }
.switch-row { justify-content: space-between; }
.set-tip { font-size: 22rpx; color: #969799; line-height: 1.6; margin-top: 12rpx; }

/* 本书操作 / 摘录 */
.opt-row { padding: 16rpx 0; display: flex; align-items: center; }
.opt-label { font-size: 28rpx; color: #323233; }
.opt-input { flex: 1; background: #f7f8fa; border-radius: 12rpx; padding: 16rpx 20rpx; font-size: 28rpx; margin-right: 16rpx; }
.opt-actions { margin-top: 8rpx; }
.opt-btn { background: #f2f3f5; color: #323233; border-radius: 999rpx; font-size: 28rpx; padding: 0 28rpx; }
.opt-btn.danger { background: #fff0f0; color: #ee0a24; }
.exc-text { background: #f7f8fa; border-radius: 16rpx; padding: 22rpx; font-size: 28rpx; color: #323233; line-height: 1.6; max-height: 240rpx; overflow: auto; margin: 8rpx 0 16rpx; }
.edit-area { height: 320rpx; }
</style>
