import { useEffect, useState } from 'react'
import { Building2 } from 'lucide-react'
import Input from '../../../components/ui/Input'
import Button from '../../../components/ui/Button'
import SettingsSection from '../../student/settings/SettingsSection'
import { updateInstitutionSettings } from '../../../api/settings'
import { showToast } from '../../../stores/toast-store'
import type { InstitutionSettings } from '../../../types'

interface OrgAccountCardProps {
  account: InstitutionSettings['account']
  onChanged: () => void
}

export default function OrgAccountCard({ account, onChanged }: OrgAccountCardProps) {
  const [name, setName] = useState(account.name ?? '')
  const [contactEmail, setContactEmail] = useState(account.contact_email ?? '')
  const [websiteUrl, setWebsiteUrl] = useState(account.website_url ?? '')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setName(account.name ?? '')
    setContactEmail(account.contact_email ?? '')
    setWebsiteUrl(account.website_url ?? '')
  }, [account.name, account.contact_email, account.website_url])

  const dirty =
    name !== (account.name ?? '') ||
    contactEmail !== (account.contact_email ?? '') ||
    websiteUrl !== (account.website_url ?? '')

  const save = async () => {
    setSaving(true)
    try {
      await updateInstitutionSettings({
        name,
        contact_email: contactEmail || undefined,
        website_url: websiteUrl || undefined,
      })
      showToast('Organization account updated', 'success')
      onChanged()
    } catch (e) {
      showToast(e instanceof Error ? e.message : 'Could not save', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <SettingsSection icon={Building2} title="Organization account">
      <div className="grid gap-3 sm:grid-cols-2">
        <Input label="Legal name" value={name} onChange={e => setName(e.target.value)} required />
        <Input
          label="Billing contact email"
          type="email"
          value={contactEmail}
          onChange={e => setContactEmail(e.target.value)}
        />
        <Input
          label="Website URL"
          value={websiteUrl}
          onChange={e => setWebsiteUrl(e.target.value)}
          placeholder="https://www.example.edu"
        />
        <Input
          label="Primary domain"
          value={account.primary_domain ?? ''}
          disabled
          helperText="Derived from your website for SES sender links."
        />
      </div>
      <div className="flex justify-end mt-2">
        <Button variant="secondary" size="sm" disabled={!dirty || saving} loading={saving} onClick={save}>
          Save
        </Button>
      </div>
    </SettingsSection>
  )
}
