import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'

const RISK = {
  low:     { label: 'AN TOÀN',          color: '#10b981', soft: 'rgba(16,185,129,0.16)' },
  medium:  { label: 'THẬN TRỌNG',       color: '#f59e0b', soft: 'rgba(245,158,11,0.16)' },
  high:    { label: 'RỦI RO CAO',       color: '#f97316', soft: 'rgba(249,115,22,0.16)' },
  extreme: { label: 'CỰC KỲ NGUY HIỂM', color: '#ef4444', soft: 'rgba(239,68,68,0.18)' },
}

const fmt = (v, unit) => {
  if (unit === '$') return '$' + Math.round(v).toLocaleString('en-US')
  return v.toLocaleString('vi-VN', { maximumFractionDigits: 1 })
}

// Dựng các path SVG từ dữ liệu dự đoán.
function buildGeometry(d) {
  const W = 640, H = 240, padX = 14, padT = 16, padB = 22
  const hist = d.history, fc = d.forecast, lo = d.band_lo, hi = d.band_hi
  const Hn = hist.length, Fn = fc.length, N = Hn + Fn
  const all = [...hist, ...fc, ...lo, ...hi]
  let min = Math.min(...all), max = Math.max(...all)
  if (min === max) { min -= 1; max += 1 }
  const pad = (max - min) * 0.14
  min -= pad; max += pad

  const X = i => padX + (i / (N - 1)) * (W - 2 * padX)
  const Y = v => H - padB - ((v - min) / (max - min)) * (H - padT - padB)
  const pp = (x, y) => `${x.toFixed(1)} ${y.toFixed(1)}`

  const histPts = hist.map((v, i) => [X(i), Y(v)])
  const fcPts = fc.map((v, i) => [X(Hn + i), Y(v)])
  const nowPt = [X(Hn - 1), Y(hist[Hn - 1])]

  const toLine = pts => pts.map((p, i) => (i ? 'L' : 'M') + pp(p[0], p[1])).join(' ')

  const histPath = toLine(histPts)
  const fcPath = 'M' + pp(nowPt[0], nowPt[1]) + ' ' + fcPts.map(p => 'L' + pp(p[0], p[1])).join(' ')
  const areaPath = histPath + ` L${pp(histPts[Hn - 1][0], H - padB)} L${pp(histPts[0][0], H - padB)} Z`

  const hiPts = hi.map((v, i) => [X(Hn + i), Y(v)])
  const loPts = lo.map((v, i) => [X(Hn + i), Y(v)])
  const cone = 'M' + pp(nowPt[0], nowPt[1]) + ' ' +
    hiPts.map(p => 'L' + pp(p[0], p[1])).join(' ') + ' ' +
    loPts.slice().reverse().map(p => 'L' + pp(p[0], p[1])).join(' ') + ' Z'

  // lưới ngang
  const grid = [0.25, 0.5, 0.75].map(f => H - padB - f * (H - padT - padB))

  return { W, H, padB, padT, histPath, fcPath, areaPath, cone, nowPt, grid, histPts, fcPts, endPt: fcPts[Fn - 1] }
}

export default function PredictPanel({ category, label }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let alive = true
    setLoading(true); setError(false)
    axios.get(`/api/predict/${category}`)
      .then(({ data }) => { if (alive) { setData(data); setLoading(false) } })
      .catch(() => { if (alive) { setError(true); setLoading(false) } })
    return () => { alive = false }
  }, [category])

  const risk = data ? (RISK[data.risk] ?? RISK.medium) : RISK.medium
  const c = risk.color

  return (
    <motion.div
      key={category}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
      className="relative mb-6 rounded-2xl border bg-slate-900/70 backdrop-blur-sm overflow-hidden"
      style={{ borderColor: c + '55', boxShadow: `0 0 40px -12px ${c}` }}
    >
      {/* glow header strip */}
      <div className="absolute inset-x-0 top-0 h-px" style={{ background: `linear-gradient(90deg,transparent,${c},transparent)` }} />

      {/* Header */}
      <div className="flex items-center justify-between gap-3 px-5 pt-4">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-lg" style={{ filter: `drop-shadow(0 0 6px ${c})` }}>🔮</span>
          <div className="min-w-0">
            <p className="text-[11px] uppercase tracking-widest text-slate-500 leading-none">Dự đoán xu hướng · {label ?? category}</p>
            <p className="text-white font-bold text-sm truncate mt-0.5">{data?.label ?? '—'}</p>
          </div>
        </div>
        <span
          className="text-[10px] font-mono px-2 py-1 rounded-md whitespace-nowrap flex-shrink-0"
          style={{ background: risk.soft, color: c, border: `1px solid ${c}55` }}
        >
          {data?.real ? '● LIVE DATA' : '◈ ƯỚC LƯỢNG'}
        </span>
      </div>

      {/* Chart */}
      <div className="px-2 pt-3">
        {loading && (
          <div className="h-[200px] flex items-center justify-center text-slate-600 text-sm animate-pulse">
            ⟳ Đang phân tích {label ?? category}...
          </div>
        )}
        {error && (
          <div className="h-[200px] flex items-center justify-center text-red-400 text-sm">
            ⚠️ Không tải được dự đoán
          </div>
        )}
        {data && !loading && <DangerChart d={data} color={c} />}
      </div>

      {/* Verdict footer */}
      {data && !loading && (
        <div className="flex items-center justify-between gap-4 px-5 py-4 border-t border-slate-700/50">
          <div className="flex items-center gap-3 min-w-0">
            <motion.span
              animate={{ opacity: [1, 0.4, 1] }}
              transition={{ repeat: Infinity, duration: 1.6 }}
              className="w-2.5 h-2.5 rounded-full flex-shrink-0"
              style={{ background: c, boxShadow: `0 0 10px ${c}` }}
            />
            <div className="min-w-0">
              <p className="font-bold text-xs uppercase tracking-wider" style={{ color: c }}>{risk.label}</p>
              <p className="text-slate-400 text-xs truncate">{data.verdict}</p>
            </div>
          </div>
          <div className="text-right flex-shrink-0">
            <p className="font-mono font-bold text-xl leading-none" style={{ color: c, textShadow: `0 0 12px ${c}66` }}>
              {data.arrow} {data.change_pct > 0 ? '+' : ''}{data.change_pct}%
            </p>
            <p className="text-[10px] text-slate-500 mt-1 font-mono">độ tin cậy {data.confidence}%</p>
          </div>
        </div>
      )}
    </motion.div>
  )
}

function DangerChart({ d, color }) {
  const g = buildGeometry(d)
  const gid = `grad-${d.category}`
  const fid = `glow-${d.category}`

  return (
    <svg viewBox={`0 0 ${g.W} ${g.H}`} className="w-full" style={{ height: 'auto' }}>
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.35" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
        <filter id={fid} x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3.5" result="b" />
          <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      {/* grid */}
      {g.grid.map((y, i) => (
        <line key={i} x1="0" x2={g.W} y1={y} y2={y} stroke="#334155" strokeOpacity="0.25" strokeWidth="1" strokeDasharray="2 5" />
      ))}

      {/* confidence cone */}
      <motion.path
        d={g.cone} fill={color} fillOpacity="0.12" stroke="none"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5, duration: 0.6 }}
      />

      {/* area under history */}
      <motion.path
        d={g.areaPath} fill={`url(#${gid})`} stroke="none"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3, duration: 0.6 }}
      />

      {/* NOW divider */}
      <line x1={g.nowPt[0]} x2={g.nowPt[0]} y1={g.padT} y2={g.H - g.padB} stroke={color} strokeOpacity="0.4" strokeWidth="1" strokeDasharray="3 3" />
      <text x={g.nowPt[0] - 4} y={g.padT + 9} textAnchor="end" fontSize="9" fill={color} fillOpacity="0.8" fontFamily="monospace">HÔM NAY</text>

      {/* history line (solid, glowing) */}
      <motion.path
        d={g.histPath} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
        filter={`url(#${fid})`}
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.1, ease: 'easeOut' }}
      />

      {/* forecast line (dashed) */}
      <motion.path
        d={g.fcPath} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeDasharray="6 5"
        filter={`url(#${fid})`}
        initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ delay: 1.0, duration: 0.9, ease: 'easeOut' }}
      />

      {/* end target dot (pulsing) */}
      <motion.circle
        cx={g.endPt[0]} cy={g.endPt[1]} r="4" fill={color} filter={`url(#${fid})`}
        animate={{ r: [4, 6.5, 4], opacity: [1, 0.5, 1] }}
        transition={{ repeat: Infinity, duration: 1.5, delay: 1.8 }}
      />
      {/* now dot */}
      <circle cx={g.nowPt[0]} cy={g.nowPt[1]} r="3" fill="#fff" />
    </svg>
  )
}
