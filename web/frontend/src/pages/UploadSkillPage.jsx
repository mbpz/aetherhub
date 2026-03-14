import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, X, FileText, AlertCircle, CheckCircle } from 'lucide-react'
import { skillsApi } from '../api'
import { toast } from '../components/Toast'
import ConfirmDialog from '../components/ConfirmDialog'
import { formatFileSize, getFileIcon } from '../lib/utils'

const CATEGORIES = ['数据处理', '网络工具', '文件操作', 'AI工具', '系统工具', '其他']
const ALLOWED_EXTS = ['.py', '.md', '.txt', '.json', '.yaml', '.yml', '.toml']
const MAX_FILE_SIZE = 10 * 1024 * 1024

function FieldError({ msg }) {
  if (!msg) return null
  return (
    <p className="text-red-500 text-xs mt-1 flex items-center gap-1">
      <AlertCircle size={12} /> {msg}
    </p>
  )
}

export default function UploadSkillPage() {
  const navigate = useNavigate()
  const fileInputRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)
  const [cancelDialog, setCancelDialog] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const [form, setForm] = useState({
    name: '', version: '1.0.0', description: '', category: '', tags: [],
  })
  const [files, setFiles] = useState([])
  const [tagInput, setTagInput] = useState('')
  const [errors, setErrors] = useState({})

  const isDirty = form.name || form.description || files.length > 0

  const updateForm = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
    setErrors((prev) => ({ ...prev, [key]: '' }))
  }

  const validate = () => {
    const errs = {}
    if (!form.name.trim()) errs.name = '技能名称不能为空'
    else if (!/^[a-zA-Z0-9\-]{2,100}$/.test(form.name)) errs.name = '名称只允许字母、数字和连字符，如 my-skill'
    if (!form.version.trim()) errs.version = '版本号不能为空'
    else if (!/^\d+\.\d+\.\d+$/.test(form.version)) errs.version = '版本号格式应为 x.y.z，如 1.0.0'
    if (files.length === 0) errs.files = '请至少上传一个文件'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const addFiles = (newFiles) => {
    const fileErrors = []
    const valid = []
    for (const f of newFiles) {
      const ext = '.' + f.name.split('.').pop().toLowerCase()
      if (!ALLOWED_EXTS.includes(ext)) {
        fileErrors.push(`不支持的文件类型：${ext}`)
        continue
      }
      if (f.size > MAX_FILE_SIZE) {
        fileErrors.push(`文件 ${f.name} 超过 10MB 大小限制`)
        continue
      }
      valid.push(f)
    }
    if (fileErrors.length > 0) {
      setErrors((prev) => ({ ...prev, fileAdd: fileErrors.join('；') }))
    } else {
      setErrors((prev) => ({ ...prev, fileAdd: '', files: '' }))
    }
    setFiles((prev) => {
      const names = new Set(prev.map((f) => f.name))
      return [...prev, ...valid.filter((f) => !names.has(f.name))]
    })
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    addFiles(Array.from(e.dataTransfer.files))
  }

  const handleAddTag = () => {
    const tag = tagInput.trim()
    if (!tag) return
    if (form.tags.length >= 10) {
      setErrors((prev) => ({ ...prev, tag: '最多只能添加 10 个标签' }))
      return
    }
    if (!form.tags.includes(tag)) {
      updateForm('tags', [...form.tags, tag])
    }
    setTagInput('')
    setErrors((prev) => ({ ...prev, tag: '' }))
  }

  const handleTagKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      handleAddTag()
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return

    setSubmitting(true)
    try {
      const formData = new FormData()
      formData.append('name', form.name)
      formData.append('version', form.version)
      if (form.description) formData.append('description', form.description)
      if (form.category) formData.append('category', form.category)
      formData.append('tags', JSON.stringify(form.tags))
      files.forEach((f) => formData.append('files', f))

      const res = await skillsApi.create(formData)
      const newId = res.data.data.id
      toast('✅ 技能上传成功！已发布到广场')
      navigate(`/skills/${newId}`, { replace: true })
    } catch (e) {
      const msg = e.response?.data?.message || '上传失败，请重试'
      if (msg.includes('already exists')) {
        setErrors((prev) => ({ ...prev, name: `技能名称 '${form.name}' 已存在，请更换名称` }))
      } else {
        toast(msg, 'error')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleCancel = () => {
    if (isDirty) setCancelDialog(true)
    else navigate(-1)
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      <button onClick={handleCancel} className="text-sm text-gray-500 hover:text-gray-800 mb-6 flex items-center gap-1">
        ← 返回
      </button>

      <h1 className="text-2xl font-bold text-gray-900 mb-8">上传新技能</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 基本信息 */}
        <div className="card p-6 space-y-5">
          <h2 className="font-semibold text-gray-900 text-lg border-b pb-3">基本信息</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              技能名称 <span className="text-red-500">*</span>
            </label>
            <input
              value={form.name}
              onChange={(e) => updateForm('name', e.target.value)}
              className={`input ${errors.name ? 'input-error' : ''}`}
              placeholder="csv-data-processor"
            />
            <p className="text-xs text-gray-400 mt-1">英文名称，字母、数字和连字符，如 my-skill</p>
            <FieldError msg={errors.name} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                版本号 <span className="text-red-500">*</span>
              </label>
              <input
                value={form.version}
                onChange={(e) => updateForm('version', e.target.value)}
                className={`input ${errors.version ? 'input-error' : ''}`}
                placeholder="1.0.0"
              />
              <FieldError msg={errors.version} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">分类</label>
              <select
                value={form.category}
                onChange={(e) => updateForm('category', e.target.value)}
                className="input"
              >
                <option value="">请选择分类</option>
                {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">技能描述</label>
            <textarea
              value={form.description}
              onChange={(e) => updateForm('description', e.target.value)}
              rows={3}
              maxLength={500}
              className="input resize-none"
              placeholder="简要介绍这个技能的功能和用途..."
            />
            <p className="text-xs text-gray-400 mt-1 text-right">{form.description.length}/500 字符</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">标签</label>
            <div className="flex flex-wrap gap-1.5 p-2.5 border border-gray-300 rounded-lg min-h-[44px] mb-2">
              {form.tags.map((tag) => (
                <span key={tag} className="tag flex items-center gap-1">
                  {tag}
                  <button type="button" onClick={() => updateForm('tags', form.tags.filter((t) => t !== tag))} className="hover:text-red-600">
                    <X size={10} />
                  </button>
                </span>
              ))}
              <input
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleTagKeyDown}
                placeholder={form.tags.length < 10 ? '输入标签，回车添加' : ''}
                disabled={form.tags.length >= 10}
                className="flex-1 min-w-24 outline-none text-sm bg-transparent"
              />
            </div>
            <div className="flex justify-between text-xs text-gray-400">
              <span>最多 10 个标签，按回车或逗号添加</span>
              <span>{form.tags.length}/10</span>
            </div>
            <FieldError msg={errors.tag} />
          </div>
        </div>

        {/* 文件上传 */}
        <div className="card p-6 space-y-4">
          <h2 className="font-semibold text-gray-900 text-lg border-b pb-3">上传文件</h2>

          {/* Drop zone */}
          <div
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
              isDragging
                ? 'border-blue-400 bg-blue-50'
                : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
            } ${errors.files ? 'border-red-400' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={32} className="mx-auto text-gray-400 mb-3" />
            <p className="font-medium text-gray-700 mb-1">拖拽文件到此处，或点击选择文件</p>
            <p className="text-sm text-gray-500">支持 {ALLOWED_EXTS.join(' ')} 格式</p>
            <p className="text-xs text-gray-400 mt-1">单文件 ≤ 10MB，总大小 ≤ 50MB</p>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept={ALLOWED_EXTS.join(',')}
              onChange={(e) => addFiles(Array.from(e.target.files))}
              className="hidden"
            />
          </div>

          <FieldError msg={errors.files} />
          {errors.fileAdd && (
            <p className="text-red-500 text-xs flex items-center gap-1">
              <AlertCircle size={12} /> {errors.fileAdd}
            </p>
          )}

          {files.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-700">已选文件：</p>
              {files.map((file, i) => (
                <div key={i} className="flex items-center gap-3 p-2.5 bg-gray-50 rounded-lg border border-gray-200">
                  <span className="text-lg">{getFileIcon(file.name)}</span>
                  <span className="flex-1 text-sm font-mono text-gray-800 truncate">{file.name}</span>
                  <span className="text-xs text-gray-400 shrink-0">{formatFileSize(file.size)}</span>
                  <button
                    type="button"
                    onClick={() => setFiles((prev) => prev.filter((_, j) => j !== i))}
                    className="text-gray-400 hover:text-red-500"
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={handleCancel} className="btn-secondary px-6">
            取消
          </button>
          <button type="submit" disabled={submitting} className="btn-primary px-8">
            {submitting ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                </svg>
                提交中...
              </span>
            ) : '提交技能'}
          </button>
        </div>
      </form>

      <ConfirmDialog
        open={cancelDialog}
        title="确认取消？"
        message="填写的内容将不会保存，确认要离开吗？"
        confirmText="确认取消"
        cancelText="继续填写"
        onConfirm={() => navigate(-1)}
        onCancel={() => setCancelDialog(false)}
      />
    </div>
  )
}
