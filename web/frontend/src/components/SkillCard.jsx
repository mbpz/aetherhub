import { Link } from 'react-router-dom'
import { Star, Download } from 'lucide-react'
import { timeAgo, getCategoryColor } from '../lib/utils'

export default function SkillCard({ skill }) {
  const tags = Array.isArray(skill.tags) ? skill.tags : []
  const visibleTags = tags.slice(0, 3)
  const extraTags = tags.length - 3

  return (
    <Link to={`/skills/${skill.id}`} className="card p-5 block group cursor-pointer">
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors truncate flex-1 pr-2">
          📦 {skill.name}
        </h3>
        {skill.version && (
          <span className="text-xs text-gray-500 shrink-0">v{skill.version}</span>
        )}
      </div>

      {skill.category && (
        <span className={`inline-block text-xs px-2 py-0.5 rounded-full mb-2 font-medium ${getCategoryColor(skill.category)}`}>
          {skill.category}
        </span>
      )}

      <p className="text-sm text-gray-600 mb-3 line-clamp-2 leading-relaxed">
        {skill.description || '暂无描述'}
      </p>

      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {visibleTags.map((tag) => (
            <span key={tag} className="tag">{tag}</span>
          ))}
          {extraTags > 0 && (
            <span className="tag bg-gray-100 text-gray-600">+{extraTags}</span>
          )}
        </div>
      )}

      <div className="flex items-center gap-3 text-xs text-gray-500 pt-2 border-t border-gray-100">
        {skill.author && (
          <div className="flex items-center gap-1.5 min-w-0">
            <img
              src={skill.author.avatar_url}
              alt={skill.author.login}
              className="w-4 h-4 rounded-full"
            />
            <span className="truncate">{skill.author.login}</span>
          </div>
        )}
        <div className="flex items-center gap-1 shrink-0">
          <Star size={12} className="text-yellow-500" />
          <span>{skill.star_count || 0}</span>
        </div>
        <span className="shrink-0">{timeAgo(skill.created_at)}</span>
      </div>
    </Link>
  )
}
