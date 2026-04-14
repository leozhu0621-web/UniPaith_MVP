import { Megaphone, GraduationCap } from 'lucide-react'
import type { InstitutionPost } from '../../../../types'

interface Props {
  post: InstitutionPost
}

export default function PostCard({ post }: Props) {
  return (
    <div className="bg-white rounded-xl border border-divider hover:shadow-sm transition-shadow overflow-hidden">
      <div className="flex items-center gap-2 px-4 pt-3 pb-1">
        <Megaphone size={12} className="text-student" />
        <span className="text-[10px] font-semibold text-student uppercase tracking-wider">School Update</span>
        <span className="text-[10px] text-student-text ml-auto">
          {new Date(post.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
        </span>
      </div>
      <div className="px-4 pb-4">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-student-mist flex items-center justify-center">
            <GraduationCap size={14} className="text-student" />
          </div>
          <span className="text-xs font-semibold text-student-ink">{(post as any).institution_name || 'School'}</span>
        </div>
        <h3 className="text-sm font-medium text-student-ink mb-1">{post.title}</h3>
        <p className="text-xs text-student-text line-clamp-3 leading-relaxed">{post.body}</p>
        {post.media_urls && post.media_urls.length > 0 && (
          <div className="mt-2 flex gap-2 overflow-x-auto">
            {post.media_urls.slice(0, 3).map((m: any, i: number) => (
              <div key={i} className="w-24 h-16 rounded-lg bg-student-mist overflow-hidden flex-shrink-0">
                <img src={typeof m === 'string' ? m : m.url} alt="" className="w-full h-full object-cover" onError={e => (e.currentTarget.style.display = 'none')} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
