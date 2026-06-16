import React, { useState } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'

const ASSETS = [
  { id: 'gold_vnd',      label: 'Vàng SJC (VND)',     asset_type: 'gold_vnd',      symbol: '',            currency: 'VND' },
  { id: 'btc',           label: 'Bitcoin (USD)',      asset_type: 'crypto',        symbol: 'bitcoin',     currency: 'USD' },
  { id: 'eth',           label: 'Ethereum (USD)',     asset_type: 'crypto',        symbol: 'ethereum',    currency: 'USD' },
  { id: 'sol',           label: 'Solana (USD)',       asset_type: 'crypto',        symbol: 'solana',      currency: 'USD' },
  { id: 'bnb',           label: 'BNB (USD)',          asset_type: 'crypto',        symbol: 'binancecoin', currency: 'USD' },
  { id: 'usd_vnd',       label: 'Tỷ giá USD/VND',     asset_type: 'exchange_rate', symbol: 'USD_VND',     currency: 'VND' },
  { id: 'gold_usd',      label: 'Vàng thế giới (USD/oz)', asset_type: 'gold_usd',  symbol: '',            currency: 'USD' },
]

// datetime-local theo giờ Việt Nam (GMT+7) hiện tại: "YYYY-MM-DDTHH:mm"
function nowVN() {
  return new Date(Date.now() + 7 * 3600 * 1000).toISOString().slice(0, 16)
}

export default function AlertForm({ onCreated, email }) {
  const [kind, setKind] = useState('price')
  const [assetId, setAssetId] = useState('gold_vnd')
  const [target, setTarget] = useState('')
  const [direction, setDirection] = useState('below')
  const [remindAt, setRemindAt] = useState(nowVN())
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)

  const submit = async (e) => {
    e.preventDefault()
    setErr(null)
    const asset = ASSETS.find(a => a.id === assetId)
    let payload
    // remind_at: input là giờ VN (GMT+7) → gắn offset +07:00 rồi chuyển ISO/UTC
    const remindIso = remindAt ? new Date(remindAt + ':00+07:00').toISOString() : null
    if (kind === 'price') {
      if (!target) { setErr('Nhập giá mục tiêu'); return }
      payload = {
        kind: 'price',
        asset_type: asset.asset_type,
        symbol: asset.symbol,
        target_value: Number(target),
        direction,
        currency: asset.currency,
        channel: 'teams',
        note: note.trim() || null,
        notify_email: email,
      }
    } else {
      if (!remindAt) { setErr('Chọn thời điểm nhắc'); return }
      payload = { kind: 'time', remind_at: remindIso, channel: 'teams', note: note.trim() || null, notify_email: email }
    }
    setBusy(true)
    try {
      await axios.post('/api/alerts', payload)
      setTarget(''); setRemindAt(nowVN()); setNote('')
      onCreated?.()
    } catch (e) {
      setErr(e?.response?.data?.detail ?? 'Tạo cảnh báo thất bại')
    } finally {
      setBusy(false)
    }
  }

  const tabCls = (active) =>
    `flex-1 py-2 rounded-lg text-sm font-medium transition-all border ${
      active
        ? 'bg-violet-600/25 border-violet-500/60 text-white'
        : 'bg-slate-700/20 border-slate-600/30 text-slate-400 hover:text-slate-300'
    }`

  return (
    <form onSubmit={submit} className="bg-slate-800/60 border border-slate-700/50 rounded-2xl p-5 backdrop-blur-sm mb-4">
      <div className="flex gap-2 mb-4">
        <button type="button" onClick={() => setKind('price')} className={tabCls(kind === 'price')}>💹 Theo giá</button>
        <button type="button" onClick={() => setKind('time')} className={tabCls(kind === 'time')}>⏰ Nhắc giờ</button>
      </div>

      {kind === 'price' ? (
        <div className="space-y-3">
          <div>
            <label className="text-slate-400 text-xs">Tài sản</label>
            <select
              value={assetId}
              onChange={e => setAssetId(e.target.value)}
              className="w-full mt-1 bg-slate-900/60 border border-slate-600/40 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500/60"
            >
              {ASSETS.map(a => <option key={a.id} value={a.id}>{a.label}</option>)}
            </select>
          </div>
          <div className="flex gap-2">
            <button type="button" onClick={() => setDirection('below')} className={tabCls(direction === 'below')}>Khi giá ≤</button>
            <button type="button" onClick={() => setDirection('above')} className={tabCls(direction === 'above')}>Khi giá ≥</button>
          </div>
          <div>
            <label className="text-slate-400 text-xs">Giá mục tiêu ({ASSETS.find(a => a.id === assetId)?.currency})</label>
            <input
              type="number" step="any" value={target}
              onChange={e => setTarget(e.target.value)}
              placeholder="vd: 140000000"
              className="w-full mt-1 bg-slate-900/60 border border-slate-600/40 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500/60"
            />
          </div>
        </div>
      ) : (
        <div>
          <label className="text-slate-400 text-xs">Thời điểm nhắc (giờ VN, GMT+7)</label>
          <input
            type="datetime-local" value={remindAt}
            onChange={e => setRemindAt(e.target.value)}
            className="w-full mt-1 bg-slate-900/60 border border-slate-600/40 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500/60"
          />
        </div>
      )}

      <div className="mt-3">
        <label className="text-slate-400 text-xs">Ghi chú (đang muốn làm gì?)</label>
        <textarea
          value={note}
          onChange={e => setNote(e.target.value)}
          rows={2}
          placeholder="vd: Mua 2 lượng vàng cưới nếu giá về mốc này"
          className="w-full mt-1 bg-slate-900/60 border border-slate-600/40 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500/60 resize-none"
        />
      </div>

      {err && <p className="text-red-400 text-xs mt-3">{err}</p>}

      <motion.button
        whileTap={{ scale: 0.97 }}
        type="submit" disabled={busy}
        className="w-full mt-4 bg-gradient-to-r from-violet-600 to-indigo-500 hover:from-violet-500 hover:to-indigo-400 disabled:opacity-50 text-white font-semibold py-2.5 rounded-xl text-sm transition-all"
      >
        {busy ? 'Đang tạo...' : '➕ Tạo cảnh báo'}
      </motion.button>
    </form>
  )
}
