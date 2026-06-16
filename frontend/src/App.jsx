import React, { useState, useCallback } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import axios from 'axios'
import Header from './components/Header'
import TodoCard from './components/TodoCard'
import PreferencesPanel from './components/PreferencesPanel'
import LoadingSkeleton from './components/LoadingSkeleton'

const INTERESTS = [
  { id: 'finance',      label: '💰 Tài chính',   desc: 'Vàng, crypto, cổ phiếu' },
  { id: 'news',         label: '📰 Tin tức',      desc: 'Thời sự trong nước' },
  { id: 'world',        label: '🌍 Thế giới',     desc: 'Tin quốc tế' },
  { id: 'tech',         label: '💻 Công nghệ',    desc: 'AI, startup, tech' },
  { id: 'sports',       label: '⚽ Thể thao',     desc: 'Bóng đá, thể thao' },
  { id: 'entertainment',label: '🎬 Giải trí',     desc: 'Phim, âm nhạc' },
  { id: 'lifestyle',    label: '🌿 Lifestyle',    desc: 'Sức khỏe, cuộc sống' },
  { id: 'work',         label: '💼 Công việc',    desc: 'Career, productivity' },
]

const CATEGORY_LABEL = {
  finance:      '💰 Tài chính',
  news:         '📰 Tin tức',
  lifestyle:    '🌿 Lifestyle',
  work:         '💼 Công việc',
  entertainment:'🎬 Giải trí',
  world:        '🌍 Thế giới',
  tech:         '💻 Tech',
  sports:       '⚽ Thể thao',
}

const PRIORITY_ORDER = { urgent: 0, normal: 1, info: 2 }

export default function App() {
  const [todos, setTodos] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [generatedAt, setGeneratedAt] = useState(null)
  const [selectedInterests, setSelectedInterests] = useState(['finance', 'news', 'tech'])
  const [filter, setFilter] = useState('all')
  const [showPrefs, setShowPrefs] = useState(false)

  const generate = useCallback(async () => {
    setLoading(true)
    setError(null)
    setFilter('all')
    try {
      const { data } = await axios.post('/api/todos/generate', {
        interests: selectedInterests,
        name: 'User',
      })
      setTodos(data.todos ?? [])
      setGeneratedAt(data.generated_at)
    } catch (e) {
      console.error(e)
      setError(
        e?.response?.data?.detail ??
        'Không thể kết nối backend. Hãy đảm bảo server đang chạy trên port 8000.'
      )
    } finally {
      setLoading(false)
    }
  }, [selectedInterests])

  // Filter + sort
  const filtered = filter === 'all' ? todos : todos.filter(t => t.category === filter)
  const sorted = [...filtered].sort(
    (a, b) => (PRIORITY_ORDER[a.priority] ?? 1) - (PRIORITY_ORDER[b.priority] ?? 1)
  )
  const categories = ['all', ...new Set(todos.map(t => t.category))]

  const urgentCount = todos.filter(t => t.priority === 'urgent').length
  const normalCount = todos.filter(t => t.priority === 'normal').length
  const infoCount   = todos.filter(t => t.priority === 'info').length

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0b1120] via-[#0f172a] to-[#0b1120]">
      <Header
        onGenerate={generate}
        loading={loading}
        generatedAt={generatedAt}
        onPreferences={() => setShowPrefs(p => !p)}
      />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {/* Preferences panel */}
        <AnimatePresence>
          {showPrefs && (
            <PreferencesPanel
              interests={INTERESTS}
              selected={selectedInterests}
              onChange={setSelectedInterests}
              onClose={() => setShowPrefs(false)}
            />
          )}
        </AnimatePresence>

        {/* Empty / welcome state */}
        {!loading && todos.length === 0 && !error && (
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex flex-col items-center justify-center py-24 text-center"
          >
            <div className="text-8xl mb-6 drop-shadow-2xl">🤖</div>
            <h2 className="text-3xl font-bold text-white mb-3">AI Todo Generator</h2>
            <p className="text-slate-400 max-w-md mb-2 leading-relaxed">
              Thay vì tự nhập todo, để AI đọc tin tức &amp; dữ liệu thị trường rồi
              tự động tạo danh sách việc cần làm cho bạn hôm nay.
            </p>
            <p className="text-slate-600 text-sm mb-8">
              Vàng giảm? Crypto pump? Cướp giật tăng? — AI sẽ nói bạn nên làm gì.
            </p>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={generate}
              className="bg-gradient-to-r from-violet-600 to-indigo-500 hover:from-violet-500 hover:to-indigo-400 text-white font-bold py-4 px-12 rounded-2xl text-lg shadow-2xl shadow-violet-500/30 transition-all"
            >
              ✨ Tạo Todo List của tôi
            </motion.button>
            <p className="text-slate-600 text-xs mt-4">
              Đang theo dõi: {selectedInterests.map(id => INTERESTS.find(i => i.id === id)?.label).join(' · ')}
            </p>
            <button
              onClick={() => setShowPrefs(true)}
              className="text-violet-400 hover:text-violet-300 text-xs mt-1 underline underline-offset-2"
            >
              Thay đổi lĩnh vực quan tâm
            </button>
          </motion.div>
        )}

        {/* Error state */}
        {error && !loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-center mb-8"
          >
            <p className="text-red-400 font-medium mb-1">⚠️ Có lỗi xảy ra</p>
            <p className="text-red-300/70 text-sm">{error}</p>
            <button
              onClick={generate}
              className="mt-4 text-sm text-red-300 hover:text-red-200 underline underline-offset-2"
            >
              Thử lại
            </button>
          </motion.div>
        )}

        {/* Loading */}
        {loading && <LoadingSkeleton />}

        {/* Todo list */}
        {!loading && todos.length > 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {/* Stats + filter bar */}
            <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-6">
              {/* Category filters */}
              <div className="flex gap-2 flex-wrap">
                {categories.map(cat => (
                  <button
                    key={cat}
                    onClick={() => setFilter(cat)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                      filter === cat
                        ? 'bg-violet-600 text-white shadow-lg shadow-violet-500/20'
                        : 'bg-slate-700/40 text-slate-400 hover:bg-slate-600/50 hover:text-slate-300'
                    }`}
                  >
                    {cat === 'all'
                      ? `🌐 Tất cả (${todos.length})`
                      : `${CATEGORY_LABEL[cat] ?? cat} (${todos.filter(t => t.category === cat).length})`}
                  </button>
                ))}
              </div>

              {/* Priority summary */}
              <div className="flex gap-2 sm:ml-auto">
                {urgentCount > 0 && (
                  <span className="text-[11px] text-red-400 bg-red-400/10 border border-red-400/20 px-2.5 py-1 rounded-full">
                    🔴 {urgentCount} khẩn
                  </span>
                )}
                {normalCount > 0 && (
                  <span className="text-[11px] text-amber-400 bg-amber-400/10 border border-amber-400/20 px-2.5 py-1 rounded-full">
                    🟡 {normalCount} nên làm
                  </span>
                )}
                {infoCount > 0 && (
                  <span className="text-[11px] text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2.5 py-1 rounded-full">
                    🟢 {infoCount} FYI
                  </span>
                )}
              </div>
            </div>

            {/* Grid */}
            <motion.div layout className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              <AnimatePresence>
                {sorted.map((todo, i) => (
                  <TodoCard key={todo.id} todo={todo} index={i} />
                ))}
              </AnimatePresence>
            </motion.div>

            {/* Bottom actions */}
            <div className="flex items-center justify-center gap-4 mt-10">
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={generate}
                className="bg-slate-700/50 hover:bg-slate-600/50 text-slate-300 font-medium py-2.5 px-7 rounded-xl border border-slate-600/40 transition-all text-sm"
              >
                🔄 Tạo lại
              </motion.button>
              <button
                onClick={() => setShowPrefs(p => !p)}
                className="text-slate-500 hover:text-slate-300 text-sm transition-colors"
              >
                ⚙️ Đổi sở thích
              </button>
            </div>
          </motion.div>
        )}
      </main>

      {/* Footer */}
      <footer className="text-center pb-8 text-slate-700 text-xs">
        AI Todo · Dữ liệu thực từ VnExpress · CafeF · CoinGecko · Yahoo Finance
      </footer>
    </div>
  )
}
