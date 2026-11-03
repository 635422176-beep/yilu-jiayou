<template>
  <view class="pg">
    <view class="hd">益禄加油</view>
    <view class="stat">
      <view class="box"><view class="num">{{ st.learned }}</view><view class="lab">已学卡片</view></view>
      <view class="box"><view class="num">{{ st.due }}</view><view class="lab">待复习</view></view>
    </view>
    <view class="row" @click="doReset">
      <text>清空学习进度</text><text class="arrow">›</text>
    </view>
    <view class="about">
      <view class="t">关于</view>
      <view class="c">吴雄志先生书目 · 中医/西医教材 · 各类歌诀，按章节知识点切分为卡片，支持翻转背诵与间隔复习（SM-2）。</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { stats, resetAll } from '../../services/cards.js'

const st = ref({ learned: 0, due: 0 })
function refresh() { st.value = stats() }
onShow(refresh)

function doReset() {
  uni.showModal({
    title: '确认清空', content: '将删除全部学习进度与排期，无法恢复。',
    success: (r) => { if (r.confirm) { resetAll(); refresh(); uni.showToast({ title: '已清空' }) } }
  })
}
</script>

<style>
.pg { padding: 24rpx; }
.hd { font-size: 38rpx; font-weight: 800; margin-bottom: 24rpx; }
.stat { display: flex; gap: 20rpx; margin-bottom: 30rpx; }
.box { flex: 1; background: #fff; border-radius: 16rpx; padding: 30rpx; text-align: center; box-shadow: 0 2rpx 12rpx rgba(0,0,0,0.05); }
.num { font-size: 48rpx; font-weight: 800; color: #07c160; }
.lab { font-size: 24rpx; color: #999; margin-top: 8rpx; }
.row { background: #fff; border-radius: 14rpx; padding: 28rpx; display: flex; justify-content: space-between; align-items: center; margin-bottom: 30rpx; }
.arrow { color: #ccc; font-size: 36rpx; }
.about { background: #fff; border-radius: 14rpx; padding: 28rpx; }
.t { font-size: 28rpx; font-weight: 700; margin-bottom: 12rpx; }
.c { font-size: 25rpx; color: #666; line-height: 1.7; }
</style>
