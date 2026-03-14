import { useState, useEffect, useCallback } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { Search, SlidersHorizontal, Package, ChevronLeft, ChevronRight } from 'lucide-react'
import { skillsApi } from '../api'
import SkillCard from '../components/SkillCard'
import { getCategoryColor } from '../lib/utils'

const SORT_OPTIONS = [
  { value: 'created_at', label: '最新上传' },
  { value: 'star_count', label: '最多 Star' },
  { value: 'download_count', label: '最多下载' },
]

function SkeletonCard() {
  return (
    <div className="card p-5 space-y-3">
      <div className="skeleton h-5 w-3/4" />
      <div className="skeleton h-4 w-1/3" />
      <div className="skeleton h-4 w-full" />
      <div className="skeleton h-4 w-2/3" />
      <div className="flex gap-2">
        <div className="skeleton h-5 w-16 rounded-full" />
        <div className="skeleton h-5 w-12 rounded-full" />
      </div>
    </div>
  )
}

export default function SkillSquarePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()

  const [skills, setSkills] = useState([])
  const [categories, setCategories] = useState([])
  const [total, setTotal] = useState(0)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [searchInput, setSearchInput] = useState(searchParams.get('q') || '')

  const q = searchParams.get('q') || ''
  const category = searchParams.get('category') || ''
  const sort = searchParams.get('sort') || 'created_at'
  const page = parseInt(searchParams.get('page') || '1', 10)

  const updateParams = (updates) => {
    const newParams = new URLSearchParams(searchParams)
    Object.entries(updates).forEach(([k, v]) => {
      if (v) newParams.set(k, v)
      else newParams.delete(k)
    })
    if ('q' in updates || 'category' in updates) newParams.set('page', '1')
    setSearchParams(newParams)
  }

  const loadSkills = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, size: 20, sort, order: 'desc' }
      if (q) params.q = q
      if (category) params.category = category
      const res = await skillsApi.list(params)
      const data = res.data.data
      setSkills(data.items)
      setTotal(data.total)
      setPages(data.pages)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [q, category, sort, page])

  const loadCategories = useCallback(async () => {
    try {
      const res = await skillsApi.categories()
      setCategories(res.data.data)
    } catch {}
  }, [])

  useEffect(() => { loadSkills() }, [loadSkills])
  useEffect(() => { loadCategories() }, [loadCategories])

  const handleSearch = (e) => {
    e.preventDefault()
    updateParams({ q: searchInput.trim() })
  }

  const clearSearch = () => {
    setSearchInput('')
    updateParams({ q: '', category: '' })
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">技能广场</h1>
          {!loading && (
            <p className="text-sm text-gray-500 mt-1">共 {total} 个技能</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">排序：</span>
          <select
            value={sort}
            onChange={(e) => updateParams({ sort: e.target.value })}
            className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Category filter */}
      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => updateParams({ category: '' })}
          className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
            !category
              ? 'bg-blue-600 text-white'
              : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'
          }`}
        >
          全部 {categories[0] ? `(${categories[0].count})` : ''}
        </button>
        {categories.slice(1).map((cat) => (
          <button
            key={cat.name}
            onClick={() => updateParams({ category: cat.name })}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
              category === cat.name
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            {cat.name} ({cat.count})
          </button>
        ))}
      </div>

      {/* Search result indicator */}
      {q && (
        <div className="flex items-center gap-2 mb-4 p-3 bg-blue-50 rounded-lg text-sm">
          <Search size={14} className="text-blue-500" />
          <span>搜索 "<strong>{q}</strong>"，共找到 {total} 个结果</span>
          <button onClick={clearSearch} className="ml-auto text-blue-600 hover:underline text-xs">
            清除搜索条件
          </button>
        </div>
      )}

      {/* Skills grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {Array.from({ length: 8 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : skills.length === 0 ? (
        <div className="text-center py-20">
          <Search size={48} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-xl font-semibold text-gray-600 mb-2">
            {q ? '未找到匹配的技能' : '暂无技能'}
          </h3>
          <p className="text-gray-500 mb-6">
            {q ? `尝试搜索 "python" 或 "数据处理"` : '成为第一个上传者吧！'}
          </p>
          <div className="flex justify-center gap-3">
            {q && (
              <button onClick={clearSearch} className="btn-secondary">
                清除搜索条件
              </button>
            )}
            <button onClick={() => navigate('/skills/upload')} className="btn-primary">
              <Package size={16} />
              上传新技能
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {skills.map((skill) => (
              <SkillCard key={skill.id} skill={skill} />
            ))}
          </div>

          {/* Pagination */}
          {pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-10">
              <button
                onClick={() => updateParams({ page: String(page - 1) })}
                disabled={page <= 1}
                className="btn-secondary disabled:opacity-40 px-3 py-2"
              >
                <ChevronLeft size={16} />
              </button>
              {Array.from({ length: Math.min(pages, 7) }, (_, i) => {
                const p = i + 1
                return (
                  <button
                    key={p}
                    onClick={() => updateParams({ page: String(p) })}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                      p === page
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    {p}
                  </button>
                )
              })}
              <button
                onClick={() => updateParams({ page: String(page + 1) })}
                disabled={page >= pages}
                className="btn-secondary disabled:opacity-40 px-3 py-2"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
