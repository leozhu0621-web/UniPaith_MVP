import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useCompareStore } from '../../stores/compare-store'
import { comparePrograms } from '../../api/saved-lists'
import Badge from '../ui/Badge'
import Button from '../ui/Button'
import Card from '../ui/Card'
import { X, ArrowRightLeft, ChevronUp, ChevronDown, GraduationCap } from 'lucide-react'

export default function CompareTray() {
  const { items, remove, clear } = useCompareStore()
  const [expanded, setExpanded] = useState(false)
  const [comparisonResult, setComparisonResult] = useState<any>(null)

  const compareMut = useMutation({
    mutationFn: () => comparePrograms(items.map(i => i.program_id)),
    onSuccess: (data) => {
      setComparisonResult(data)
      setExpanded(true)
    },
  })

  if (items.length === 0) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40">
      {expanded && comparisonResult && (
        <div className="bg-white border-t border-gray-200 shadow-lg max-h-[60vh] overflow-y-auto">
          <div className="max-w-5xl mx-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-stone-700">Side-by-Side Comparison</h3>
              <button onClick={() => setExpanded(false)} className="text-gray-400 hover:text-gray-600">
                <X size={18} />
              </button>
            </div>
            {comparisonResult.ai_analysis && (
              <Card className="p-4 mb-4 bg-stone-50">
                <p className="text-sm text-stone-700">{comparisonResult.ai_analysis}</p>
              </Card>
            )}
            {comparisonResult.comparison_data && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 px-3 text-xs text-gray-500 font-medium">Field</th>
                      {items.map(item => (
                        <th key={item.program_id} className="text-left py-2 px-3 text-xs text-stone-700 font-semibold">
                          {item.program_name}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(comparisonResult.comparison_data as Record<string, Record<string, string>>).map(([field, values]) => (
                      <tr key={field} className="border-b border-gray-100">
                        <td className="py-2 px-3 text-xs text-gray-500 font-medium capitalize">
                          {field.replace(/_/g, ' ')}
                        </td>
                        {items.map(item => (
                          <td key={item.program_id} className="py-2 px-3 text-xs text-stone-700">
                            {String(values[item.program_id] ?? '—')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="bg-stone-800 text-white shadow-lg">
        <div className="max-w-5xl mx-auto px-4 py-2.5 flex items-center gap-3">
          <ArrowRightLeft size={16} className="text-stone-400 flex-shrink-0" />
          <span className="text-xs text-stone-400 flex-shrink-0">Compare</span>

          <div className="flex items-center gap-2 flex-1 overflow-x-auto">
            {items.map(item => (
              <span
                key={item.program_id}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-stone-700 rounded-full text-xs whitespace-nowrap flex-shrink-0"
              >
                <GraduationCap size={12} className="text-stone-400" />
                <span className="max-w-[140px] truncate">{item.program_name}</span>
                {item.degree_type && (
                  <Badge variant="info" size="sm">{item.degree_type}</Badge>
                )}
                <button
                  onClick={() => remove(item.program_id)}
                  className="text-stone-500 hover:text-white"
                >
                  <X size={12} />
                </button>
              </span>
            ))}
            {items.length < 5 && (
              <span className="text-[10px] text-stone-500 flex-shrink-0">
                {5 - items.length} more slots
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <Button
              size="sm"
              onClick={() => compareMut.mutate()}
              disabled={items.length < 2 || compareMut.isPending}
              loading={compareMut.isPending}
              className="bg-white text-stone-800 hover:bg-gray-100"
            >
              Compare ({items.length})
            </Button>
            {comparisonResult && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="p-1 text-stone-400 hover:text-white"
              >
                {expanded ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
              </button>
            )}
            <button onClick={clear} className="text-stone-500 hover:text-white text-xs">
              Clear
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
