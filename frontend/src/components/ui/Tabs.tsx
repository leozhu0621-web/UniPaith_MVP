import clsx from 'clsx'

// Tabs — Spec/02 §10 + Spec/02b §3.3. On mobile this scrolls horizontally as a
// segmented control; selection stays deep-linkable (consumer writes ?tab=).
interface Tab {
  id: string
  label: string
  count?: number
}

interface TabsProps {
  tabs: Tab[]
  activeTab: string
  onChange: (tabId: string) => void
}

export default function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div
      role="tablist"
      className="flex border-b border-border overflow-x-auto no-scrollbar flex-nowrap"
    >
      {tabs.map(tab => {
        const active = activeTab === tab.id
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(tab.id)}
            className={clsx(
              'ui-btn shrink-0 px-4 py-2.5 text-sm font-semibold transition-colors border-b-2 -mb-px whitespace-nowrap',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-t-md',
              active
                ? 'border-secondary text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            )}
          >
            {tab.label}
            {tab.count != null && (
              <span
                className={clsx(
                  'ml-1.5 px-1.5 py-0.5 text-xs rounded-pill',
                  active ? 'bg-cobalt/10 text-cobalt' : 'bg-muted text-muted-foreground'
                )}
              >
                {tab.count}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
