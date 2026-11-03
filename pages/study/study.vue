<template>
  <view class="pg">
    <view class="top">
      <text class="prog">{{ idx + 1 }} / {{ deck.length }}</text>
      <text class="tt">{{ chapter }}</text>
    </view>

    <view class="card" @click="reveal" v-if="!revealed">
      <view class="front">{{ cur.front }}</view>
      <view class="hint">点击显示背面 · 🔊可诵读</view>
    </view>
    <view class="card" v-else>
      <view class="front">{{ cur.front }}</view>
      <view class="div"></view>
      <view class="back">{{ cur.back }}</view>
    </view>

    <view class="ctrls">
      <button class="btn ghost" @click="speak">🔊 诵读</button>
      <button class="btn primary" v-if="!revealed" @click="reveal">显示背面</button>
      <template v-else>
        <button class="btn again" @click="grade(1)">忘了</button>
        <button class="btn mid" @click="grade(3)">模糊</button>
        <button class="btn ok" @click="grade(5)">记得</button>
      </template>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { loadBookCards, getDeck, gradeCard } from '../../services/cards.js'

const deck = ref([])
const idx = ref(0)
const revealed = ref(false)
const chapter = ref('')
const cur = computed(() => deck.value[idx.value] || {})

onLoad(async (opt) => {
  const bookId = decodeURIComponent(opt.bookId || '')
  chapter.value = opt.chapter ? decodeURIComponent(opt.chapter) : '全部'
  const cards = await loadBookCards(bookId)
  deck.value = getDeck(cards, { chapterTitle: opt.chapter ? chapter.value : null })
  if (!deck.value.length) uni.showToast({ title: '该章无卡片', icon: 'none' })
})

function reveal() { revealed.value = true }

function speak() {
  const txt = revealed.value
    ? cur.value.front + '。' + cur.value.back
    : cur.value.front
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    const u = new SpeechSynthesisUtterance(txt)
    u.lang = 'zh-CN'; u.rate = 0.9
    window.speechSynthesis.cancel(); window.speechSynthesis.speak(u)
  } else {
    uni.showToast({ title: '当前端暂不支持朗读', icon: 'none' })
  }
}

function grade(g) {
  gradeCard(cur.value.id, g, {
    bookId: cur.value.bookId,
    front: cur.value.front,
    type: cur.value.type,
    chapterTitle: cur.value.chapterTitle
  })
  if (idx.value < deck.value.length - 1) {
    idx.value++; revealed.value = false
  } else {
    uni.showToast({ title: '本章学完 🎉', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 700)
  }
}
</script>

<style>
.pg { padding: 24rpx; display: flex; flex-direction: column; min-height: 100%; box-sizing: border-box; }
.top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20rpx; }
.prog { font-size: 26rpx; color: #999; }
.tt { font-size: 28rpx; color: #323233; font-weight: 600; }
.card {
  flex: 1; background: #fff; border-radius: 20rpx; padding: 40rpx 36rpx;
  box-shadow: 0 4rpx 24rpx rgba(0,0,0,0.06);
  display: flex; flex-direction: column; justify-content: center;
}
.front { font-size: 40rpx; line-height: 1.7; color: #1a1a1a; font-weight: 600; }
.hint { margin-top: 30rpx; color: #bbb; font-size: 24rpx; }
.div { height: 2rpx; background: #eee; margin: 28rpx 0; }
.back { font-size: 32rpx; line-height: 1.8; color: #444; white-space: pre-wrap; }
.ctrls { display: flex; gap: 16rpx; margin-top: 24rpx; }
.btn { flex: 1; font-size: 28rpx; border-radius: 14rpx; padding: 22rpx 0; border: none; color: #fff; }
.ghost { background: #f2f3f5; color: #555; }
.primary { background: #07c160; }
.again { background: #ee0a24; }
.mid { background: #ff976a; }
.ok { background: #1989fa; }
</style>
