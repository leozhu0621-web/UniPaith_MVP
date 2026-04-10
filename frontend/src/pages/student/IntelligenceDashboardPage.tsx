import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getMatches } from '../../api/matching'
import { getOnboarding } from '../../api/students'
import apiClient from '../../api/client'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import ProgressBar from '../../components/ui/ProgressBar'
import Skeleton from '../../components/ui/Skeleton'
import {
  TrendingUp, Brain, Sparkles, AlertCircle, CheckCircle2,
  Download, Share2, Eye, Target, BarChart3,
} from 'lucide-react'

const getCompletionMap = () => apiClient.get('/students/me/completion-map').then(r => r.data)
const getInsightsConfidence = () => apiClient.get('/students/me/insights/confidence').then(r => r.data)
const getPortableExport = () => apiClient.get('/students/me/profile/portable-export').then(r => r.data)

export default function IntelligenceDashboardPage() {
  const navigate = useNavigate()
  const [exportData, setExportData] = useState<any>(null)

  useQuery({ queryKey: ['onboarding'], queryFn: getOnboarding })
  const { data: completionMap } = useQuery({ queryKey: ['completion-map'], queryFn: getCompletionMap, retry: false })
  const { data: insights, isLoading: insLoading } = useQuery({ queryKey: ['insights-confidence'], queryFn: getInsightsConfidence, retry: false })
  const { data: matches } = useQuery({ queryKey: ['matches'], queryFn: () => getMatches(), retry: false })

  const matchesList: any[] = Array.isArray(matches) ? matches : []
  const sections: any[] = completionMap?.sections ?? []
  const highInsights: any[] = insights?.high_confidence ?? []
  const lowInsights: any[] = insights?.low_confidence ?? []

  const handleExport = async () => {
    const data = await getPortableExport()
    setExportData(data)
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'unipaith-profile.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-stone-700">Intelligence Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">AI insights about your profile and matches</p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="secondary" onClick={handleExport}>
            <Download size={14} className="mr-1" /> Export Profile
          </Button>
          <Button size="sm" variant="secondary" onClick={() => navigate('/s/intake')}>
            <Sparkles size={14} className="mr-1" /> Quick Start
          </Button>
        </div>
      </div>

      {/* Progressive Completion (#54) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <Target size={16} className="text-stone-600" />
            <h3 className="text-sm font-medium text-stone-700">Match Ready</h3>
            <Badge variant={completionMap?.match_ready ? 'success' : 'warning'} size="sm">
              {completionMap?.match_ready_pct ?? 0}%
            </Badge>
          </div>
          <ProgressBar value={completionMap?.match_ready_pct ?? 0} />
          <p className="text-xs text-gray-500 mt-2">Direction + constraints + academics needed for AI matching</p>
        </Card>
        <Card className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle2 size={16} className="text-stone-600" />
            <h3 className="text-sm font-medium text-stone-700">Apply Ready</h3>
            <Badge variant={completionMap?.apply_ready ? 'success' : 'info'} size="sm">
              {completionMap?.apply_ready_pct ?? 0}%
            </Badge>
          </div>
          <ProgressBar value={completionMap?.apply_ready_pct ?? 0} />
          <p className="text-xs text-gray-500 mt-2">All sections needed for program-specific applications</p>
        </Card>
      </div>

      {/* Section Completion Grid */}
      {sections.length > 0 && (
        <Card className="p-4">
          <h3 className="text-sm font-medium text-stone-700 mb-3">Profile Sections</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {sections.map((s: any) => (
              <div key={s.key} className={`p-3 rounded-lg text-center ${s.done ? 'bg-emerald-50' : 'bg-gray-50'}`}>
                <p className="text-xs font-medium text-stone-700">{s.name}</p>
                <Badge variant={s.done ? 'success' : 'neutral'} size="sm" className="mt-1">
                  {s.done ? 'Complete' : 'Incomplete'}
                </Badge>
                {s.match_required && <p className="text-[10px] text-amber-600 mt-0.5">Match required</p>}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Confidence Scoring (#55) + Multi-Source Signals (#56) */}
      <Card className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Brain size={16} className="text-stone-600" />
          <h3 className="text-sm font-medium text-stone-700">AI Confidence</h3>
          <span className="text-xs text-gray-400">{insights?.total ?? 0} insights extracted</span>
        </div>
        {insLoading ? <Skeleton className="h-20" /> : (
          <div className="space-y-3">
            {highInsights.length > 0 && (
              <div>
                <p className="text-xs font-medium text-emerald-700 mb-1">High Confidence ({highInsights.length})</p>
                <div className="flex flex-wrap gap-1.5">
                  {highInsights.slice(0, 8).map((i: any) => (
                    <span key={i.id} className="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-emerald-50 text-emerald-700 rounded-full">
                      <CheckCircle2 size={10} />{i.type}: {i.text.slice(0, 40)}{i.text.length > 40 ? '...' : ''}
                      <Badge variant="neutral" size="sm">{i.source}</Badge>
                    </span>
                  ))}
                </div>
              </div>
            )}
            {lowInsights.length > 0 && (
              <div>
                <p className="text-xs font-medium text-amber-700 mb-1">
                  <AlertCircle size={12} className="inline mr-1" />
                  Needs Clarification ({lowInsights.length})
                </p>
                <div className="space-y-1">
                  {lowInsights.map((i: any) => (
                    <div key={i.id} className="flex items-center justify-between bg-amber-50 rounded px-2 py-1">
                      <span className="text-xs text-amber-700">{i.type}: {i.text.slice(0, 60)}</span>
                      <Badge variant="warning" size="sm">{Math.round(i.confidence * 100)}%</Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {insights?.total === 0 && (
              <p className="text-sm text-gray-500">No AI insights yet. Complete your profile or use the Quick Start chat to build your AI understanding.</p>
            )}
          </div>
        )}
      </Card>

      {/* Match Score Evolution (#57) */}
      <Card className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <TrendingUp size={16} className="text-stone-600" />
          <h3 className="text-sm font-medium text-stone-700">Match Intelligence</h3>
        </div>
        {matchesList.length > 0 ? (
          <div className="space-y-2">
            <p className="text-xs text-gray-500">{matchesList.length} programs matched</p>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="bg-emerald-50 rounded-lg p-3">
                <p className="text-lg font-bold text-emerald-700">
                  {matchesList.filter((m: any) => m.match_tier === 3).length}
                </p>
                <p className="text-xs text-gray-500">Strong Fit</p>
              </div>
              <div className="bg-amber-50 rounded-lg p-3">
                <p className="text-lg font-bold text-amber-700">
                  {matchesList.filter((m: any) => m.match_tier === 2).length}
                </p>
                <p className="text-xs text-gray-500">Good Fit</p>
              </div>
              <div className="bg-stone-50 rounded-lg p-3">
                <p className="text-lg font-bold text-stone-700">
                  {matchesList.filter((m: any) => m.match_tier === 1).length}
                </p>
                <p className="text-xs text-gray-500">Possible Fit</p>
              </div>
            </div>
            <Button size="sm" variant="secondary" onClick={() => navigate('/s/match')} className="mt-2">
              <BarChart3 size={14} className="mr-1" /> View Match Details
            </Button>
          </div>
        ) : (
          <div className="text-center py-4">
            <Eye size={24} className="text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-500">Complete your profile to 80% to see AI matches</p>
            <Button size="sm" variant="secondary" onClick={() => navigate('/s/profile')} className="mt-2">
              Complete Profile
            </Button>
          </div>
        )}
      </Card>

      {/* Portability (#58) */}
      <Card className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Share2 size={16} className="text-stone-600" />
          <h3 className="text-sm font-medium text-stone-700">Profile Portability</h3>
        </div>
        <p className="text-sm text-gray-600 mb-3">
          Your UniPaith profile is a portable artifact you own. Export it as JSON to reuse across institutions or keep as a personal record.
        </p>
        <div className="flex gap-2">
          <Button size="sm" onClick={handleExport}>
            <Download size={14} className="mr-1" /> Download JSON
          </Button>
        </div>
        {exportData && (
          <p className="text-xs text-emerald-600 mt-2">
            <CheckCircle2 size={12} className="inline mr-1" />Profile exported successfully
          </p>
        )}
      </Card>
    </div>
  )
}
