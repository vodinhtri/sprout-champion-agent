import React from 'react'
import { motion } from 'framer-motion'

const tips = [
  'Đang đọc VnExpress & CafeF...',
  'Kiểm tra giá Bitcoin & Ethereum...',
  'Xem giá vàng hôm nay...',
  'Phân tích xu hướng thị trường...',
  'Claude AI đang suy nghĩ...',
  'Tổng hợp danh sách việc cần làm...',
]

function SkeletonCard({ delay }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="rounded-2xl border border-slate-700/30 bg-slate-800/20 p-5 space-y-3"
    >
      <div className="flex gap-2">
        <div className="w-6 h-6 bg-slate-700/50 rounded-lg animate-pulse" />
        <div className="w-24 h-5 bg-slate-700/50 rounded-full animate-pulse" />
        <div className="ml-auto w-16 h-5 bg-slate-700/30 rounded-md animate-pulse" />
      </div>
      <div className="w-3/4 h-5 bg-slate-700/50 rounded animate-pulse" />
      <div className="space-y-1.5">
        <div className="w-full h-3 bg-slate-700/30 rounded animate-pulse" />
        <div className="w-5/6 h-3 bg-slate-700/30 rounded animate-pulse" />
      </div>
      <div className="border-t border-slate-700/30 pt-3">
        <div className="w-full h-3 bg-slate-700/20 rounded animate-pulse" />
      </div>
    </motion.div>
  )
}

export default function LoadingSkeleton() {
  const [tipIdx, setTipIdx] = React.useState(0)

  React.useEffect(() => {
    const iv = setInterval(() => setTipIdx(i => (i + 1) % tips.length), 1400)
    return () => clearInterval(iv)
  }, [])

  return (
    <div>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-10"
      >
        <div className="text-5xl mb-4 animate-bounce">🤖</div>
        <p className="text-violet-300 font-medium">{tips[tipIdx]}</p>
        <p className="text-slate-600 text-xs mt-1">Thường mất 5-10 giây</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {[0, 0.08, 0.16, 0.24, 0.32, 0.4].map((delay, i) => (
          <SkeletonCard key={i} delay={delay} />
        ))}
      </div>
    </div>
  )
}
