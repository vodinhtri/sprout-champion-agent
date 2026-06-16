import React, { useCallback, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'
import AlertForm from './AlertForm'
import AlertList from './AlertList'

const EMAIL_KEY = 'alert_notify_email'
const VNG_EMAIL = /^[a-zA-Z0-9._%+-]+@vng\.com\.vn$/

export default function AlertsPanel({ onClose }) {
  const [alerts, setAlerts] = useState([])
  const [checking, setChecking] = useState(false)
  const [email, setEmail] = useState(() => localStorage.getItem(EMAIL_KEY) || '')
  const [editingEmail, setEditingEmail] = useState(false)
  const [draftEmail, setDraftEmail] = useState('')
  const [emailErr, setEmailErr] = useState(null)

  const refresh = useCallback(async () => {
    try {
      const { data } = await axios.get('/api/alerts')
      setAlerts(Array.isArray(data) ? data : [])
    } catch (e) {
      console.error(e)
    }
  }, [])

  useEffect(() => {
    refresh()
    const t = setInterval(refresh, 60000)
    return () => clearInterval(t)
  }, [refresh])

  const checkNow = async () => {
    setChecking(true)
    try {
      await axios.post('/api/alerts/check-now')
      await refresh()
    } finally {
      setChecking(false)
    }
  }

  const saveEmail = (e) => {
    e.preventDefault()
    const v = draftEmail.trim()
    if (!VNG_EMAIL.test(v)) {
      setEmailErr('Email phải dạng abc@vng.com.vn')
      return
    }
    localStorage.setItem(EMAIL_KEY, v)
    setEmail(v)
    setEditingEmail(false)
    setEmailErr(null)
  }

  const needEmail = !email || editingEmail

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
            <h3 className="text-white font-semibold">🔔 Cảnh báo giá &amp; nhắc giờ</h3>
            <p className="text-slate-500 text-xs mt-0.5">Đặt mốc giá hoặc giờ → nhận thông báo qua Teams</p>
          </div>
          <div className="flex items-center gap-3">
            {!needEmail && (
              <button
                onClick={checkNow}
                disabled={checking}
                className="text-violet-400 hover:text-violet-300 text-xs underline underline-offset-2 disabled:opacity-50"
              >
                {checking ? 'Đang kiểm tra...' : 'Kiểm tra ngay'}
              </button>
            )}
            <button onClick={onClose} className="text-slate-500 hover:text-white text-sm transition-colors">✕</button>
          </div>
        </div>

        {needEmail ? (
          <form onSubmit={saveEmail} className="bg-slate-700/20 border border-slate-600/30 rounded-xl p-4">
            <label className="text-slate-300 text-sm font-medium">Email VNG của bạn (để Teams @mention)</label>
            <p className="text-slate-500 text-xs mt-0.5 mb-2">Chỉ cần nhập 1 lần, lưu lại trên trình duyệt này.</p>
            <input
              type="email"
              autoFocus
              value={draftEmail}
              onChange={e => setDraftEmail(e.target.value)}
              placeholder="trivd@vng.com.vn"
              className="w-full bg-slate-900/60 border border-slate-600/40 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-violet-500/60"
            />
            {emailErr && <p className="text-red-400 text-xs mt-2">{emailErr}</p>}
            <button
              type="submit"
              className="w-full mt-3 bg-gradient-to-r from-violet-600 to-indigo-500 hover:from-violet-500 hover:to-indigo-400 text-white font-semibold py-2 rounded-xl text-sm transition-all"
            >
              Lưu &amp; tiếp tục
            </button>
          </form>
        ) : (
          <>
            <div className="flex items-center justify-between mb-3 text-xs">
              <span className="text-slate-400">👤 Thông báo tới <span className="text-slate-200">{email}</span></span>
              <button
                onClick={() => { setDraftEmail(email); setEditingEmail(true) }}
                className="text-violet-400 hover:text-violet-300 underline underline-offset-2"
              >
                Đổi email
              </button>
            </div>
            <AlertForm onCreated={refresh} email={email} />
            <AlertList alerts={alerts} onChanged={refresh} />
          </>
        )}
      </div>
    </motion.div>
  )
}
