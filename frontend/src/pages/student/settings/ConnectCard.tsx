import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Users } from 'lucide-react'
import Toggle from '../../../components/ui/Toggle'
import Skeleton from '../../../components/ui/Skeleton'
import SettingsSection, { SettingRow } from './SettingsSection'
import { getPreferences, upsertPreferences } from '../../../api/students'
import { showToast } from '../../../stores/toast-store'

// Spec 20 §2 — Connect preferences. Auto-follow an institution when you save one
// of its programs, so its updates/events surface in Connect.
export default function ConnectCard() {
  const queryClient = useQueryClient()
  const { data: prefs, isLoading } = useQuery({
    queryKey: ['student-preferences'],
    queryFn: getPreferences,
    retry: false,
  })

  const saveMut = useMutation({
    mutationFn: (autoFollow: boolean) => upsertPreferences({ auto_follow_on_save: autoFollow }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['student-preferences'] })
      queryClient.invalidateQueries({ queryKey: ['connect-follows'] })
      queryClient.invalidateQueries({ queryKey: ['connect-feed'] })
      showToast('Connect preferences saved', 'success')
    },
    onError: () => showToast("Something didn't work. Try again.", 'error'),
  })

  const autoFollow = prefs?.auto_follow_on_save ?? true

  return (
    <SettingsSection icon={Users} title="Connect">
      {isLoading ? (
        <Skeleton className="h-12 rounded-lg" />
      ) : (
        <SettingRow
          label="Auto-follow when I save a program"
        >
          <Toggle
            checked={autoFollow}
            onChange={v => saveMut.mutate(v)}
            disabled={saveMut.isPending}
            label="Auto-follow on save"
          />
        </SettingRow>
      )}
    </SettingsSection>
  )
}
