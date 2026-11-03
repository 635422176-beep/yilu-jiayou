// utils/review.js
// SM-2 间隔重复算法（Anki 同款逻辑），纯函数，前端 / 云函数均可复用，可单测。
// 数据模型约定：每张卡片对应用户的个性化排期 { ease, interval, repetitions, dueDate }

const MIN_EASE = 1.3;

/**
 * 计算下一次复习排期
 * @param {Object} prev 上一次进度 { ease, interval, repetitions }
 * @param {number} grade 本次评分 0-5（0=完全忘了 ~ 5=秒回；<3 视为未记住，需重学）
 * @param {Date} [today] 基准日期，默认今天
 * @returns {{ ease:number, interval:number, repetitions:number, dueDate:Date }}
 */
export function scheduleNext(prev, grade, today = new Date()) {
  const ease = prev?.ease ?? 2.5;
  const interval = prev?.interval ?? 0;
  const repetitions = prev?.repetitions ?? 0;

  let nextEase = ease;
  let nextInterval;
  let nextReps;

  if (grade < 3) {
    // 没记住：重置进度，明天再学
    nextReps = 0;
    nextInterval = 1;
  } else {
    if (repetitions === 0) {
      nextInterval = 1;
    } else if (repetitions === 1) {
      nextInterval = 6;
    } else {
      nextInterval = Math.round(interval * ease);
    }
    nextReps = repetitions + 1;
    // 难度因子（ease）按评分更新：越接近 5 越容易，最低 1.3
    nextEase = ease + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02));
    if (nextEase < MIN_EASE) nextEase = MIN_EASE;
  }

  const dueDate = new Date(today);
  dueDate.setDate(dueDate.getDate() + nextInterval);
  dueDate.setHours(0, 0, 0, 0);

  return { ease: nextEase, interval: nextInterval, repetitions: nextReps, dueDate };
}

/**
 * 判断某卡片今日是否到期（含逾期）
 */
export function isDue(schedule, today = new Date()) {
  const d = new Date(today);
  d.setHours(0, 0, 0, 0);
  const due = new Date(schedule.dueDate);
  due.setHours(0, 0, 0, 0);
  return due <= d;
}

/**
 * 生成新卡片的初始排期（首次学习后调用，grade 通常为新学评分）
 */
export function initSchedule(grade, today = new Date()) {
  return scheduleNext({ ease: 2.5, interval: 0, repetitions: 0 }, grade, today);
}
