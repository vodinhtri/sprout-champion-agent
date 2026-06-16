import React from 'react'
import { motion } from 'framer-motion'

export default function PreferencesPanel({ interests, selected, onChange, onClose }) {
  const toggle = (id) => {
    if (selected.includes(id)) {
      if (selected.length > 1) onChange(selected.filter(i => i !== id))
    } else {
      onChange([...selected, id])
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      className="overflow-hidden mb-6"
    >
      <div className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-5 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-white font-semibold">🎯 Lĩnh vực quan tâm</h3>
            <p className="text-slate-500 text-xs mt-0.5">AI sẽ ưu tiên dữ liệu theo những gì bạn chọn</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-white text-sm transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          {interests.map(item => {
            const active = selected.includes(item.id)
            return (
              <button
                key={item.id}
                onClick={() => toggle(item.id)}
                className={`p-3 rounded-xl text-left transition-all border ${
                  active
                    ? 'bg-violet-600/25 border-violet-500/60 text-white'
                    : 'bg-slate-700/20 border-slate-600/30 text-slate-400 hover:border-slate-500/60 hover:text-slate-300'
                }`}
              >
                <div className="font-medium text-sm">{item.label}</div>
                <div className="text-[11px] opacity-60 mt-0.5 leading-tight">{item.desc}</div>
              </button>
            )
          })}
        </div>

        <p className="text-slate-600 text-xs mt-3">
          Đang chọn {selected.length}/{interests.length} lĩnh vực · Nhấn "Tạo Todo" để áp dụng
        </p>
      </div>
    </motion.div>
  )
}
