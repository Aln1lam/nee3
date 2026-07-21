/** 转为 YYYY-MM-DD（本地日历日） */
export function dateKeyFrom(input) {
  if (!input) return null
  const d = input instanceof Date
    ? input
    : new Date(typeof input === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(input) ? `${input}T12:00:00` : input)
  if (Number.isNaN(d.getTime())) return null
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function addDaysToKey(key, days) {
  const d = new Date(`${key}T12:00:00`)
  d.setDate(d.getDate() + days)
  return dateKeyFrom(d)
}

/**
 * FullCalendar 全天事件：end 为 exclusive（末日的下一天）
 * @param {boolean} opts.endExclusive - end 是否已是 FC exclusive 格式
 */
export function toFcAllDaySpan(start, end, opts = {}) {
  const startKey = dateKeyFrom(start)
  if (!startKey) return null

  let lastInclusive = startKey
  if (end) {
    const endKey = dateKeyFrom(end)
    if (endKey) {
      lastInclusive = opts.endExclusive ? addDaysToKey(endKey, -1) : endKey
    }
  }
  if (lastInclusive < startKey) lastInclusive = startKey

  return {
    start: startKey,
    end: addDaysToKey(lastInclusive, 1),
    allDay: true,
  }
}

export function buildFcAllDayEvent(base, start, end, opts = {}) {
  const span = toFcAllDaySpan(start, end, opts)
  if (!span) return null
  return { ...base, ...span }
}
