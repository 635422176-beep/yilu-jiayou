<template>
  <view class="pg">
    <view class="hd">今日复习（{{ list.length }}）</view>
    <view v-if="!list.length" class="empty">暂无到期卡片，去书架学几张吧～</view>
    <view v-for="c in list" :key="c.id" class="item" @click="go(c)">
      <view class="q">{{ c.front }}</view>
      <view class="meta">{{ c.bookId }} · {{ c.chapterTitle }}</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { dueStudied } from '../../services/cards.js'

const list = ref([])
function refresh() { list.value = dueStudied() }
onShow(refresh)

function go(c) {
  uni.navigateTo({
    url: '/pages/study/study?bookId=' + encodeURIComponent(c.bookId) +
         '&chapter=' + encodeURIComponent(c.chapterTitle || '')
  })
}
</script>

<style>
.pg { padding: 24rpx; }
.hd { font-size: 32rpx; font-weight: 700; margin-bottom: 20rpx; }
.empty { color: #999; font-size: 28rpx; padding: 60rpx 0; text-align: center; }
.item { background: #fff; border-radius: 14rpx; padding: 26rpx; margin-bottom: 16rpx; box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.05); }
.q { font-size: 30rpx; color: #1a1a1a; font-weight: 600; }
.meta { font-size: 24rpx; color: #999; margin-top: 10rpx; }
</style>
