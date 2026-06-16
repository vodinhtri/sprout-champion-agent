import React, { useState } from 'react'
import { motion } from 'framer-motion'

const PRIORITY = {
  urgent: {
    label: '🔴 Khẩn cấp',
    border: 'border-red-500/40',
    bg: 'bg-red-500/5',
    shadow: 'shadow-red-500/10',
    accent: 'text-red-400',
    dot: 'bg-red-500',
    ring: 'ring-red-500/20',
  },
  normal: {
    label: '🟡 Nên làm',
    border: 'border-amber-500/40',
    bg: 'bg-amber-500/5',
    shadow: 'shadow-amber-500/10',
    accent: 'text-amber-400',
    dot: 'bg-amber-400',
    ring: 'ring-amber-500/20',
  },
  info: {
    label: '🟢 Để biết',
    border: 'border-emerald-500/30',
    bg: 'bg-emerald-500/5',
    shadow: 'shadow-emerald-500/10',
    accent: 'text-emerald-400',
    dot: 'bg-emerald-500',
    ring: 'ring-emerald-500/20',
  },
}

const CATEGORY_ICON = {
  finance:      '💰',
  news:         '📰',
  lifestyle:    '🌿',
  work:         '💼',
  entertainment:'🎬',
  world:        '🌍',
  tech:         '💻',
  sports:       '⚽',
}

export default function TodoCard({ todo, index }) {
  const [done, setDone] = useState(false)
  const cfg = PRIORITY[todo.priority] ?? PRIORITY.info

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ delay: index * 0.07, duration: 0.4, ease: 'easeOut' }}
      onClick={() => setDone(d => !d)}
      className={`
        relative rounded-2xl border ${cfg.border} ${cfg.bg}
        backdrop-blur-sm p-5 shadow-lg ${cfg.shadow}
        cursor-pointer group transition-all duration-200
        hover:scale-[1.025] hover:ring-1 ${cfg.ring}
        ${done ? 'opacity-40' : ''}
      `}
    >
      {/* Top row */}
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xl">{CATEGORY_ICON[todo.category] ?? '📌'}</span>
          <span className={`text-[11px] font-semibold ${cfg.accent} bg-white/5 px-2 py-0.5 rounded-full`}>
            {cfg.label}
          </span>
        </div>
        {todo.data_point && (
          <span className="text-[11px] font-mono text-slate-400 bg-slate-700/50 px-2 py-0.5 rounded-md whitespace-nowrap flex-shrink-0">
            {todo.data_point}
          </span>
        )}
      </div>

      {/* Title */}
      <h3 className={`text-white font-bold text-[15px] mb-2 leading-snug ${done ? 'line-through text-slate-500' : ''}`}>
        {todo.title}
      </h3>

      {/* Action */}
      <div className="flex items-start gap-2 mb-3">
        <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} mt-[5px] flex-shrink-0`} />
        <p className="text-slate-300 text-sm leading-relaxed">{todo.action}</p>
      </div>

      {/* Rationale */}
      <p className="text-slate-500 text-xs leading-relaxed border-t border-slate-700/40 pt-3">
        💡 {todo.rationale}
      </p>

      {/* Done overlay */}
      {done && (
        <div className="absolute inset-0 flex items-center justify-center rounded-2xl pointer-events-none">
          <span className="text-5xl drop-shadow-lg">✅</span>
        </div>
      )}
    </motion.div>
  )
}
