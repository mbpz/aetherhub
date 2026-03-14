import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Plus, Package, Trash2, Eye, Star } from 'lucide-react'
import { skillsApi } from '../api'
import { useAuthStore } from '../store/authStore'
import ConfirmDialog from '../components/ConfirmDialog'
import { toast } from '../components/Toast'
import { timeAgo, getCategoryColor } from '../lib/utils'

function SkeletonCard() {
  return (
    <div className="card p-5 space-y-3">
      <div className="skeleton h-5 w-3/4" />
      <div className="skeleton h-4 w-1/3" />
      <div className="skeleton h-4 w-full" />
      <div className="skeleton h-8 w-full" />
    </div>
  )
}

export default function MySkillsPage() {
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const [skills, setSkills] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleteLoading, setDeleteLoading] = useState(false)

  useEffect(() => { loadSkills() }, [])

  const loadSkills = async () => {
    setLoading(true)
    try {
      const res = await skillsApi.mine()
      setSkills(res.data.data.items)
      setTotal(res.data.data.total)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    setDeleteLoading(true)
    try {
      await skillsApi.delete(deleteTarget.id)
      setSkills((prev) => prev.filter((s) => s.id !== deleteTarget.id))
      setTotal((t) => t - 1)
      toast('技能已成功删除')
    } catch {
      toast('删除失败，请重试', 'error')
    } finally {
      setDeleteLoading(false)
      setDeleteTarget(null)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">我的技能</h1>
          {!loading && (
            <p className="text-sm text-gray-500 mt-1">共 {total} 个技能</p>
          )}
        </div>
        <Link to="/skills/upload" className="btn-primary">
          <Plus size={16} />
          上传新技能
        </Link>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : skills.length === 0 ? (
        <div className="text-center py-24">
          <Package size={60} className="mx-auto text-gray-300 mb-5" />
          <h2 className="text-xl font-semibold text-gray-600 mb-2">你还没有上传任何技能</h2>
          <p className="text-gray-500 mb-6">分享你的技能，让更多人受益！</p>
          <Link to="/skills/upload" className="btn-primary text-sm">
            <Plus size={16} />
            立即上传第一个技能
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {skills.map((skill) => (
            <div key={skill.id} className="card p-5 flex flex-col">
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-gray-900 truncate flex-1 pr-2">
                  📦 {skill.name}
                </h3>
                <span className="text-xs text-gray-500 shrink-0">v{skill.version}</span>
              </div>

              {skill.category && (
                <span className={`self-start text-xs px-2 py-0.5 rounded-full mb-2 font-medium ${getCategoryColor(skill.category)}`}>
                  {skill.category}
                </span>
              )}

              <p className="text-sm text-gray-600 mb-3 line-clamp-2 flex-1">
                {skill.description || '暂无描述'}
              </p>

              {skill.tags?.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {skill.tags.slice(0, 3).map((tag) => (
                    <span key={tag} className="tag text-xs">{tag}</span>
                  ))}
                </div>
              )}

              <div className="flex items-center justify-between text-xs text-gray-500 mb-4 pt-2 border-t border-gray-100">
                <div className="flex items-center gap-1">
                  <Star size={11} className="text-yellow-500" />
                  <span>{skill.star_count}</span>
                </div>
                <span className={`px-2 py-0.5 rounded-full text-xs ${skill.is_public ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                  {skill.is_public ? '已公开' : '私有'}
                </span>
                <span>{timeAgo(skill.created_at)}</span>
              </div>

              <div className="flex gap-2">
                <Link to={`/skills/${skill.id}`} className="btn-secondary flex-1 justify-center text-sm py-1.5">
                  <Eye size={14} />
                  查看详情
                </Link>
                <button
                  onClick={() => setDeleteTarget(skill)}
                  className="btn-danger px-3 py-1.5 text-sm"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        title="确认删除"
        message={`你确定要删除技能 "${deleteTarget?.name}" 吗？此操作不可撤销，技能将从平台永久移除。`}
        confirmText="确认删除"
        cancelText="取消"
        danger
        loading={deleteLoading}
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  )
}
