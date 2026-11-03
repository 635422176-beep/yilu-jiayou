<template>
  <view class="page">
    <view class="head">
      <text class="title">导入资料</text>
      <text class="sub">把书稿按章节整理进阅读器。支持粘贴文字或上传 .txt / .md 文件（自动识别「第X章 / 一、 / 1. / # 标题」分章）。PDF / Word 原文件请直接交给我，我来切分排版后导入。</text>
    </view>

    <view class="card">
      <view class="row">
        <text class="label">书名</text>
        <input class="inp" v-model="bookTitle" placeholder="留空则自动取首行" />
      </view>
      <view class="row">
        <text class="label">分类</text>
        <input class="inp" v-model="category" placeholder="如：中医 / 内科 / 笔记" />
      </view>
      <textarea class="area" v-model="text" placeholder="在此粘贴书稿……&#10;示例：&#10;# 中医基础&#10;## 第一章 阴阳五行&#10;阴阳者，天地之道也……&#10;## 第二章 脏腑&#10;……&#10;（也可不用 #，直接写「第一章 标题」也会被识别）" maxlength="-1" />
      <view class="actions">
        <button class="btn ghost" @click="chooseFile">上传 .txt/.md</button>
        <button class="btn" @click="doImport">解析并导入</button>
      </view>
      <text class="hint" v-if="hint">{{ hint }}</text>
    </view>

    <view class="card">
      <text class="card-title">已导入书本（{{ books.length }}）</text>
      <view v-if="!books.length" class="empty">还没有自建书本。</view>
      <view v-for="b in books" :key="b.id" class="bk-item">
        <view class="bk-info">
          <text class="bk-name">{{ b.title }}</text>
          <text class="bk-meta">{{ (b.category || '未分类') }} · {{ b.chapters.length }} 章</text>
        </view>
        <text class="bk-del" @click="del(b.id)">删除</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { addUserBook, removeUserBook, getAllBookMeta } from '../../services/content.js'

const bookTitle = ref('')
const category = ref('')
const text = ref('')
const hint = ref('')
const books = ref([])

function refresh() { books.value = getAllBookMeta().filter(b => b._user) }
onShow(() => refresh())

// 解析：支持 Markdown 标题层级 与 中文章节标记，输出 { title, chapters:[{id,title,paras,sections}] }
function parseBook(rawTitle, rawCat, src) {
  const lines = (src || '').split(/\r?\n/).map(l => l.replace(/\s+$/, ''))
  let title = (rawTitle || '').trim() || '未命名书稿'
  const chapters = []
  let curChap = null
  let curSec = null
  let foundAny = false

  for (const line of lines) {
    const s = line.trim()
    if (!s) continue
    const md = s.match(/^(#{1,6})\s+(.*)$/)
    if (md) {
      const lvl = md[1].length
      const txt = md[2].trim()
      if (lvl === 1) { if (!rawTitle.trim()) title = txt; continue }
      if (lvl === 2) {
        curChap = { id: 'c_' + Date.now() + '_' + chapters.length, title: txt, paras: [], sections: [] }
        chapters.push(curChap); curSec = null; foundAny = true; continue
      }
      if (lvl >= 3) {
        if (!curChap) { curChap = { id: 'c_' + Date.now(), title: '正文', paras: [], sections: [] }; chapters.push(curChap); foundAny = true }
        curSec = { title: txt, paras: [] }
        curChap.sections.push(curSec); continue
      }
    }
    // 中文 / 数字章节标记
    if (/^第\s*[0-9零一二三四五六七八九十百]+\s*[章回节篇卷]/.test(s) ||
        /^[一二三四五六七八九十]+、/.test(s) ||
        /^[0-9]+[.、]/.test(s)) {
      curChap = { id: 'c_' + Date.now() + '_' + chapters.length, title: s, paras: [], sections: [] }
      chapters.push(curChap); curSec = null; foundAny = true; continue
    }
    if (!curChap) {
      curChap = { id: 'c_' + Date.now(), title: title || '正文', paras: [], sections: [] }
      chapters.push(curChap)
    }
    const target = curSec || curChap
    target.paras.push(s)
  }
  if (!chapters.length && !foundAny && title === '未命名书稿') {
    // 纯文本无标题：整体作为一章
    chapters.push({ id: 'c_' + Date.now(), title: title, paras: lines.filter(l => l.trim()) })
  }
  return { title, chapters }
}

function doImport() {
  if (!text.value.trim()) { hint.value = '请先粘贴或上传书稿内容。'; return }
  const parsed = parseBook(bookTitle.value, category.value, text.value)
  if (!parsed.chapters.length) { hint.value = '未能识别到任何章节，请检查格式。'; return }
  const book = {
    id: 'b_' + Date.now(),
    title: parsed.title,
    category: (category.value || '').trim() || '导入',
    chapters: parsed.chapters,
    _user: true
  }
  addUserBook(book)
  hint.value = '已导入《' + book.title + '》，共 ' + book.chapters.length + ' 章。去「原著」阅读。'
  bookTitle.value = ''; category.value = ''; text.value = ''
  refresh()
}

function chooseFile() {
  // H5 / Electron 下读取本地文本文件
  uni.chooseFile({
    count: 1,
    type: 'file',
    extension: ['.txt', '.md', '.text'],
    success: (res) => {
      const f = (res.tempFiles && res.tempFiles[0]) || null
      if (!f) return
      const url = f.path || f.url
      if (!url) { hint.value = '无法读取该文件，请改用粘贴方式。'; return }
      fetch(url).then(r => r.text()).then(t => {
        text.value = t
        if (!bookTitle.value.trim() && f.name) bookTitle.value = f.name.replace(/\.(txt|md|text)$/i, '')
        hint.value = '已读取文件，点「解析并导入」即可。'
      }).catch(() => { hint.value = '读取失败，请改用粘贴方式。' })
    },
    fail: () => { hint.value = '选择文件失败，请改用粘贴方式。' }
  })
}

function del(id) {
  removeUserBook(id)
  refresh()
}
</script>

<style scoped>
.page { min-height: 100vh; background: #f5f5f5; padding: 28rpx 28rpx 60rpx; box-sizing: border-box; }
.head { padding: 8rpx 8rpx 20rpx; }
.title { font-size: 38rpx; font-weight: 700; color: #323233; display: block; }
.sub { font-size: 24rpx; color: #969799; line-height: 1.6; margin-top: 10rpx; display: block; }
.card { background: #fff; border-radius: 20rpx; padding: 28rpx; margin-top: 20rpx; }
.row { display: flex; align-items: center; margin-bottom: 16rpx; }
.label { font-size: 28rpx; color: #323233; width: 110rpx; flex-shrink: 0; }
.inp { flex: 1; background: #f7f8fa; border-radius: 12rpx; padding: 18rpx 22rpx; font-size: 28rpx; }
.area { width: 100%; height: 360rpx; background: #f7f8fa; border-radius: 12rpx; padding: 22rpx; box-sizing: border-box; font-size: 28rpx; color: #323233; line-height: 1.6; }
.actions { display: flex; gap: 18rpx; margin-top: 18rpx; }
.btn { flex: 1; background: #07c160; color: #fff; border-radius: 999rpx; font-size: 30rpx; }
.btn.ghost { background: #f2f3f5; color: #323233; }
.hint { display: block; font-size: 24rpx; color: #07c160; margin-top: 16rpx; line-height: 1.6; }
.card-title { font-size: 30rpx; font-weight: 700; color: #323233; display: block; margin-bottom: 12rpx; }
.empty { font-size: 26rpx; color: #c8c9cc; padding: 20rpx 0; }
.bk-item { display: flex; align-items: center; padding: 22rpx 0; border-bottom: 1rpx solid #f2f3f5; }
.bk-info { flex: 1; display: flex; flex-direction: column; }
.bk-name { font-size: 30rpx; color: #323233; }
.bk-meta { font-size: 22rpx; color: #969799; margin-top: 4rpx; }
.bk-del { font-size: 26rpx; color: #ee0a24; }
</style>
