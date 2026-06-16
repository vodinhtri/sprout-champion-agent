import React from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import axios from 'axios'

function fmt(v, currency) {
  if (v == null) return '—'
  return `${Number(v).toLocaleString('vi-VN')}${currency ? ' ' + currency : ''}`
}

// hiển thị thời điểm theo giờ VN (GMT+7)
function fmtVN(iso) {
  if (!iso) return '—'
  const d = new Date(new Date(iso).getTime() + 7 * 3600 * 1000)
  return d.toISOString().slice(0, 16).replace('T', ' ') + ' (GMT+7)'
}

function describe(a) {
  if (a.kind === 'time') {
    return `Nhắc lúc ${fmtVN(a.remind_at)}`
  }
  return `${a.label || 'Cảnh báo'} ${a.last_value != null ? `· hiện tại ${fmt(a.last_value, a.currency)}` : ''}`
}

export default function AlertList({ alerts, onChanged }) {
  const remove = async (id) => {
    await axios.delete(`/api/alerts/${id}`)
    onChanged?.()
  }

  if (!alerts.length) {
    return <p className="text-slate-500 text-sm text-center py-4">Chưa có cảnh báo nào.</p>
  }

  const active = alerts.filter(a => a.status === 'active')
  const triggered = alerts.filter(a => a.status === 'triggered')

  const row = (a) => (
    <motion.div
      key={a.id}
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -10 }}
      className={`flex items-center justify-between gap-3 p-3 rounded-xl border ${
        a.status === 'triggered'
          ? 'bg-emerald-500/10 border-emerald-500/40'
          : 'bg-slate-700/20 border-slate-600/30'
      }`}
    >
      <div className="min-w-0">
        <div className="text-sm text-white truncate">
          {a.status === 'triggered' ? '🔔 ' : (a.kind === 'time' ? '⏰ ' : '💹 ')}
          {describe(a)}
        </div>
        {a.note && (
          <div className="text-[11px] text-slate-400 mt-0.5 truncate">📝 {a.note}</div>
        )}
        <div className="text-[11px] text-slate-500">
          {a.status === 'triggered' ? `Đã báo · ${fmtVN(a.last_triggered_at)}` : 'Đang theo dõi'}
        </div>
      </div>
      <button
        onClick={() => remove(a.id)}
        className="text-slate-500 hover:text-red-400 text-sm flex-shrink-0 transition-colors"
        title="Xoá"
      >✕</button>
    </motion.div>
  )

  return (
    <div className="space-y-4">
      {active.length > 0 && (
        <div className="space-y-2">
          <p className="text-slate-400 text-xs font-medium">Đang theo dõi ({active.length})</p>
          <AnimatePresence>{active.map(row)}</AnimatePresence>
        </div>
      )}
      {triggered.length > 0 && (
        <div className="space-y-2">
          <p className="text-emerald-400 text-xs font-medium">Đã kích hoạt ({triggered.length})</p>
          <AnimatePresence>{triggered.map(row)}</AnimatePresence>
        </div>
      )}
    </div>
  )
}
