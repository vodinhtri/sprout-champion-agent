import React from 'react'
import { motion } from 'framer-motion'

function timeAgo(isoStr) {
  if (!isoStr) return null
  const seconds = Math.floor((Date.now() - new Date(isoStr)) / 1000)
  if (seconds < 60) return 'vừa xong'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} phút trước`
  return `${Math.floor(seconds / 3600)} giờ trước`
}

export default function Header({ onGenerate, loading, generatedAt, onPreferences, onAlerts }) {
  const ago = timeAgo(generatedAt)

  return (
    <header className="sticky top-0 z-50 border-b border-slate-700/40 bg-slate-900/80 backdrop-blur-xl">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-4">
        {/* Logo */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <div className="w-9 h-9 bg-gradient-to-br from-violet-600 to-indigo-500 rounded-xl flex items-center justify-center text-lg shadow-lg shadow-violet-500/30">
            🤖
          </div>
          <div>
            <h1 className="text-white font-bold text-lg leading-none">Momentum</h1>
            <p className="text-slate-500 text-[10px] leading-none mt-0.5">Powered by Claude</p>
          </div>
        </div>

        {/* Right actions */}
        <div className="flex items-center gap-2">
          {ago && (
            <span className="text-slate-500 text-xs hidden sm:block">
              Cập nhật {ago}
            </span>
          )}
          <button
            onClick={onAlerts}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-700/60 transition-all"
            title="Cảnh báo giá & nhắc giờ"
          >
            🔔
          </button>
          <button
            onClick={onPreferences}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-700/60 transition-all"
            title="Tùy chọn sở thích"
          >
            ⚙️
          </button>
          <motion.button
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            onClick={onGenerate}
            disabled={loading}
            className="flex items-center gap-2 bg-gradient-to-r from-violet-600 to-indigo-500 hover:from-violet-500 hover:to-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-2 px-4 rounded-xl text-sm transition-all shadow-lg shadow-violet-500/20"
          >
            {loading ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin inline-block" />
                Đang phân tích...
              </>
            ) : (
              '✨ Tạo Todo'
            )}
          </motion.button>
        </div>
      </div>
    </header>
  )
}
