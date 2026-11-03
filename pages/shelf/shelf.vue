<template>
  <view class="pg">
    <view class="hd">益禄加油 · 卡片书架</view>
    <view v-for="g in tree" :key="g.group" class="grp">
      <view class="gh" @click="tg(g.group)">{{ g.group }}（{{ g.books.length }}）</view>
      <view v-if="openG[g.group]">
        <view v-for="b in g.books" :key="b.id" class="bk">
          <view class="bh" @click="tb(b)">{{ b.title }} <text class="muted">· {{ b.chapterCount }}章</text></view>
          <view v-if="openB[b.id] && chaps[b.id]">
            <view v-for="ch in chaps[b.id]" :key="ch.title" class="ch" @click="start(b.id, ch.title)">
              {{ ch.title }} <text class="muted">({{ ch.cards.length }})</text>
            </view>
          </view>
          <view v-if="openB[b.id] && !chaps[b.id]" class="ld">加载中…</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { loadManifest, buildTree, loadBookCards, chaptersOf } from '../../services/cards.js'

const tree = ref([])
const openG = ref({})
const openB = ref({})
const chaps = ref({})

onMounted(async () => {
  const m = await loadManifest()
  tree.value = buildTree(m)
})

function tg(g) { openG.value[g] = !openG.value[g] }
async function tb(b) {
  openB.value[b.id] = !openB.value[b.id]
  if (openB.value[b.id] && !chaps.value[b.id]) {
    const cards = await loadBookCards(b.id)
    chaps.value[b.id] = chaptersOf(cards)
  }
}
function start(bookId, chapter) {
  uni.navigateTo({
    url: '/pages/study/study?bookId=' + encodeURIComponent(bookId) +
         '&chapter=' + encodeURIComponent(chapter)
  })
}
</script>

<style>
.pg { padding: 20rpx 24rpx 60rpx; }
.hd { font-size: 34rpx; font-weight: 700; padding: 16rpx 0 24rpx; color: #323233; }
.grp { margin-bottom: 12rpx; }
.gh { font-size: 30rpx; font-weight: 700; color: #07c160; padding: 18rpx 12rpx; background: #f0faf3; border-radius: 12rpx; }
.bk { margin: 8rpx 0 8rpx 12rpx; }
.bh { font-size: 28rpx; padding: 14rpx 12rpx; color: #323233; }
.ch { font-size: 27rpx; padding: 12rpx 12rpx 12rpx 36rpx; color: #555; border-left: 4rpx solid #e8e8e8; margin-left: 8rpx; }
.muted { color: #999; font-size: 24rpx; }
.ld { color: #999; font-size: 24rpx; padding: 12rpx 12rpx 12rpx 36rpx; }
</style>
