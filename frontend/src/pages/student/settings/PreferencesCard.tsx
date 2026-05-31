import { SlidersHorizontal, Sun, Moon, Monitor } from 'lucide-react'
import clsx from 'clsx'
import Select from '../../../components/ui/Select'
import Toggle from '../../../components/ui/Toggle'
import SettingsSection, { SettingRow } from './SettingsSection'
import { useThemeStore, type Theme, type FontSize } from '../../../stores/theme-store'
import type { SettingsPreferences } from '../../../types'
import type { UpdateSettingsPayload } from '../../../api/settings'

const LOCALES = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Español' },
  { value: 'fr', label: 'Français' },
  { value: 'de', label: 'Deutsch' },
  { value: 'pt', label: 'Português' },
  { value: 'zh', label: '中文' },
  { value: 'hi', label: 'हिन्दी' },
  { value: 'ar', label: 'العربية' },
  { value: 'ja', label: '日本語' },
  { value: 'ko', label: '한국어' },
]

const TIMEZONES = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'America/Sao_Paulo',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Africa/Lagos',
  'Asia/Dubai',
  'Asia/Kolkata',
  'Asia/Shanghai',
  'Asia/Singapore',
  'Asia/Tokyo',
  'Australia/Sydney',
].map(z => ({ value: z, label: z.replace(/_/g, ' ') }))

const THEME_OPTIONS: { value: Theme; label: string; icon: typeof Sun }[] = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
]

const FONT_OPTIONS: { value: FontSize; label: string }[] = [
  { value: 'sm', label: 'S' },
  { value: 'md', label: 'M' },
  { value: 'lg', label: 'L' },
  { value: 'xl', label: 'XL' },
]

interface PreferencesCardProps {
  preferences: SettingsPreferences
  onSave: (payload: UpdateSettingsPayload) => void
  saving?: boolean
}

export default function PreferencesCard({ preferences, onSave, saving }: PreferencesCardProps) {
  const theme = useThemeStore()

  const setTheme = (t: Theme) => {
    theme.setTheme(t) // instant visual feedback
    onSave({ theme: t })
  }
  const setFont = (f: FontSize) => {
    theme.setFontSize(f)
    onSave({ font_size: f })
  }
  const setDyslexia = (v: boolean) => {
    theme.setDyslexia(v)
    onSave({ dyslexia_mode: v })
  }
  const setReduce = (v: boolean) => {
    theme.setReduceMotion(v)
    onSave({ reduced_motion: v })
  }

  return (
    <SettingsSection
      icon={SlidersHorizontal}
      title="Preferences"
      description="Language, timezone, theme, and accessibility."
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Select
          label="Language"
          options={LOCALES}
          value={preferences.locale ?? 'en'}
          onChange={e => onSave({ locale: e.target.value })}
          disabled={saving}
          helperText="The language UniPaith speaks to you in."
        />
        <Select
          label="Timezone"
          options={TIMEZONES}
          placeholder="Select timezone"
          value={preferences.timezone ?? ''}
          onChange={e => onSave({ timezone: e.target.value })}
          disabled={saving}
          helperText="Normalizes all deadlines & calendar times."
        />
      </div>

      <div className="border-t border-border mt-2 pt-1 divide-y divide-border">
        <SettingRow label="Theme" description="Light, dark, or follow your system.">
          <Segmented
            value={theme.theme}
            options={THEME_OPTIONS.map(o => ({ value: o.value, label: o.label, icon: o.icon }))}
            onChange={v => setTheme(v as Theme)}
          />
        </SettingRow>
        <SettingRow label="Text size" description="Scales text across the app.">
          <Segmented
            value={theme.fontSize}
            options={FONT_OPTIONS}
            onChange={v => setFont(v as FontSize)}
          />
        </SettingRow>
        <SettingRow
          label="Dyslexia-friendly"
          description="Roomier spacing + a high-legibility typeface."
        >
          <Toggle checked={theme.dyslexia} onChange={setDyslexia} label="Dyslexia-friendly mode" />
        </SettingRow>
        <SettingRow label="Reduce motion" description="Minimizes animations and transitions.">
          <Toggle checked={theme.reduceMotion} onChange={setReduce} label="Reduce motion" />
        </SettingRow>
      </div>
    </SettingsSection>
  )
}

function Segmented({
  value,
  options,
  onChange,
}: {
  value: string
  options: { value: string; label: string; icon?: typeof Sun }[]
  onChange: (v: string) => void
}) {
  return (
    <div className="inline-flex rounded-lg border border-border bg-muted p-0.5" role="group">
      {options.map(o => {
        const active = o.value === value
        const Icon = o.icon
        return (
          <button
            key={o.value}
            type="button"
            onClick={() => onChange(o.value)}
            aria-pressed={active}
            className={clsx(
              'ui-btn inline-flex items-center gap-1.5 rounded-md px-3 h-8 text-[13px] font-medium transition-colors',
              active
                ? 'bg-card text-foreground elev-subtle'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            {Icon && <Icon size={14} />}
            {o.label}
          </button>
        )
      })}
    </div>
  )
}
