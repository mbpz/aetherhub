import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Star, Trash2, ArrowLeft, Copy, Check, ExternalLink } from 'lucide-react'
import { skillsApi } from '../api'
import { useAuthStore } from '../store/authStore'
import MarkdownViewer from '../components/MarkdownViewer'
import ConfirmDialog from '../components/ConfirmDialog'
import { toast } from '../components/Toast'
import { timeAgo, formatFileSize, getFileIcon, getCategoryColor } from '../lib/utils'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

const LANG_MAP = {
  py: 'python', md: 'markdown', json: 'json', yaml: 'yaml', yml: 'yaml',
  toml: 'toml', txt: 'text',
}

function getLang(filename) {
  const ext = filename?.split('.').pop()?.toLowerCase()
  return LANG_MAP[ext] || 'text'
}

export default function SkillDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { isLoggedIn, user } = useAuthStore()

  const [skill, setSkill] = useState(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [activeTab, setActiveTab] = useState('readme')
  const [viewingFile, setViewingFile] = useState(null)
  const [fileContent, setFileContent] = useState('')
  const [fileLoading, setFileLoading] = useState(false)
  const [starLoading, setStarLoading] = useState(false)
  const [deleteDialog, setDeleteDialog] = useState(false)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    loadSkill()
  }, [id])

  const loadSkill = async () => {
    setLoading(true)
    try {
      const res = await skillsApi.getById(id)
      setSkill(res.data.data)
    } catch (e) {
      if (e.response?.status === 404) setNotFound(true)
    } finally {
      setLoading(false)
    }
  }

  const handleStar = async () => {
    if (!isLoggedIn) {
      toast('请登录后才能 Star 技能', 'error')
      return
    }
    setStarLoading(true)
    try {
      if (skill.is_starred) {
        const res = await skillsApi.unstar(id)
        setSkill((prev) => ({ ...prev, ...res.data.data }))
      } else {
        const res = await skillsApi.star(id)
        setSkill((prev) => ({ ...prev, ...res.data.data }))
      }
    } catch {
      toast('操作失败，请重试', 'error')
    } finally {
      setStarLoading(false)
    }
  }

  const handleDelete = async () => {
    setDeleteLoading(true)
    try {
      await skillsApi.delete(id)
      toast('技能已删除')
      navigate('/mine', { replace: true })
    } catch {
      toast('删除失败', 'error')
    } finally {
      setDeleteLoading(false)
      setDeleteDialog(false)
    }
  }

  const handleViewFile = async (file) => {
    setViewingFile(file)
    setFileLoading(true)
    try {
      const res = await skillsApi.getFileContent(id, file.filename)
      setFileContent(res.data)
    } catch {
      setFileContent('// 无法加载文件内容')
    } finally {
      setFileLoading(false)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(fileContent)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-10">
        <div className="animate-pulse space-y-4">
          <div className="skeleton h-8 w-1/2" />
          <div className="skeleton h-4 w-1/4" />
          <div className="skeleton h-32 w-full" />
        </div>
      </div>
    )
  }

  if (notFound) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-20 text-center">
        <div className="text-5xl mb-4">🔍</div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">技能不存在</h2>
        <p className="text-gray-500 mb-6">该技能可能已被删除或 ID 有误</p>
        <Link to="/skills" className="btn-primary">返回广场</Link>
      </div>
    )
  }

  if (!skill) return null

  const skillMdContent = skill.skill_md || skill.files?.find(f => f.filename.toLowerCase() === 'skill.md') ? skill.skill_md : null

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      {/* Back */}
      <button onClick={() => navigate(-1)} className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 mb-6">
        <ArrowLeft size={16} />
        返回广场
      </button>

      {/* Skill header card */}
      <div className="card p-6 mb-6">
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1 flex-wrap">
              <h1 className="text-2xl font-bold text-gray-900">📦 {skill.name}</h1>
              <span className="text-sm text-gray-500 shrink-0">v{skill.version}</span>
            </div>
            {skill.category && (
              <span className={`inline-block text-xs px-2.5 py-1 rounded-full font-medium ${getCategoryColor(skill.category)}`}>
                {skill.category}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleStar}
              disabled={starLoading}
              className={`btn text-sm px-4 py-2 ${
                skill.is_starred
                  ? 'bg-yellow-400 text-white hover:bg-yellow-500'
                  : 'btn-secondary'
              }`}
            >
              <Star size={15} fill={skill.is_starred ? 'currentColor' : 'none'} />
              {skill.is_starred ? '已 Star' : 'Star'} ({skill.star_count})
            </button>
            {skill.is_author && (
              <button
                onClick={() => setDeleteDialog(true)}
                className="btn-danger text-sm px-3 py-2"
              >
                <Trash2 size={15} />
                删除
              </button>
            )}
          </div>
        </div>

        {skill.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {skill.tags.map((tag) => (
              <span key={tag} className="tag">{tag}</span>
            ))}
          </div>
        )}

        {skill.description && (
          <p className="text-gray-600 mb-4 leading-relaxed">{skill.description}</p>
        )}

        <div className="flex items-center gap-4 text-sm text-gray-500 pt-3 border-t border-gray-100">
          {skill.author && (
            <a
              href={skill.author.html_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 hover:text-blue-600"
            >
              <img src={skill.author.avatar_url} alt={skill.author.login} className="w-5 h-5 rounded-full" />
              {skill.author.name || skill.author.login}
              <ExternalLink size={12} />
            </a>
          )}
          <span>📅 {skill.created_at ? new Date(skill.created_at).toLocaleDateString('zh-CN') : ''}</span>
          <span>更新于 {timeAgo(skill.updated_at)}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="flex border-b border-gray-200">
          {[
            { key: 'readme', label: 'README' },
            { key: 'files', label: `文件 (${skill.files?.length || 0})` },
            { key: 'skill_md', label: 'SKILL.md' },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => { setActiveTab(tab.key); setViewingFile(null) }}
              className={`px-6 py-3 text-sm font-medium transition-colors border-b-2 ${
                activeTab === tab.key
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="p-6">
          {activeTab === 'readme' && (
            <MarkdownViewer content={skill.readme || '*该技能暂未提供 README 文档。*'} />
          )}

          {activeTab === 'files' && (
            <>
              {viewingFile ? (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <span>{getFileIcon(viewingFile.filename)}</span>
                      <span>{viewingFile.filename}</span>
                      <span className="text-gray-400">({formatFileSize(viewingFile.file_size)})</span>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={handleCopy} className="btn-secondary text-xs px-3 py-1.5">
                        {copied ? <Check size={13} /> : <Copy size={13} />}
                        {copied ? '已复制' : '复制全部'}
                      </button>
                      <button onClick={() => setViewingFile(null)} className="btn-ghost text-xs px-3 py-1.5">
                        ← 返回列表
                      </button>
                    </div>
                  </div>
                  {fileLoading ? (
                    <div className="text-center py-10 text-gray-400">加载中...</div>
                  ) : getLang(viewingFile.filename) === 'markdown' ? (
                    <MarkdownViewer content={fileContent} />
                  ) : (
                    <SyntaxHighlighter
                      language={getLang(viewingFile.filename)}
                      style={vscDarkPlus}
                      showLineNumbers
                      className="rounded-lg text-sm"
                    >
                      {fileContent}
                    </SyntaxHighlighter>
                  )}
                </div>
              ) : (
                <div className="space-y-2">
                  {skill.files?.length === 0 && <p className="text-gray-500">暂无文件</p>}
                  {skill.files?.map((file) => (
                    <div
                      key={file.id}
                      className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 border border-gray-100"
                    >
                      <span className="text-lg">{getFileIcon(file.filename)}</span>
                      <span className="flex-1 font-mono text-sm text-gray-800">{file.filename}</span>
                      <span className="text-xs text-gray-400">{formatFileSize(file.file_size)}</span>
                      <button
                        onClick={() => handleViewFile(file)}
                        className="btn-secondary text-xs px-3 py-1"
                      >
                        查看
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {activeTab === 'skill_md' && (
            skill.skill_md ? (
              <MarkdownViewer content={skill.skill_md} />
            ) : (
              <div className="flex items-center gap-2 text-gray-500 py-6">
                <span className="text-xl">⚠️</span>
                <span>该技能尚未提供 SKILL.md 规格说明。</span>
              </div>
            )
          )}
        </div>
      </div>

      <ConfirmDialog
        open={deleteDialog}
        title="确认删除"
        message={`你确定要删除技能 "${skill.name}" 吗？此操作不可撤销，技能将从平台永久移除。`}
        confirmText="确认删除"
        cancelText="取消"
        danger
        loading={deleteLoading}
        onConfirm={handleDelete}
        onCancel={() => setDeleteDialog(false)}
      />
    </div>
  )
}
