import { LogOut } from 'lucide-react'
import Button from '../../../components/ui/Button'
import SettingsSection from './SettingsSection'
import { useAuthStore } from '../../../stores/auth-store'

export default function SignOutCard() {
  const logout = useAuthStore(s => s.logout)

  return (
    <SettingsSection
      icon={LogOut}
      title="Sign out"
    >
      <Button variant="tertiary" onClick={logout}>
        <LogOut size={14} /> Sign out
      </Button>
    </SettingsSection>
  )
}
