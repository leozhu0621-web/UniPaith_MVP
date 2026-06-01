import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, Trash2, ShieldOff, Plus } from 'lucide-react'
import Sheet from '../../../components/ui/Sheet'
import Button from '../../../components/ui/Button'
import Input from '../../../components/ui/Input'
import Textarea from '../../../components/ui/Textarea'
import Toggle from '../../../components/ui/Toggle'
import Badge from '../../../components/ui/Badge'
import Skeleton from '../../../components/ui/Skeleton'
import {
  getUploadedLists,
  createUploadedList,
  deleteUploadedList,
  getSuppressions,
  addSuppression,
  deleteSuppression,
  getInstitution,
  updateInstitution,
} from '../../../api/institutions'
import type { UploadedList, CampaignSuppression, Institution } from '../../../types'
import { showToast } from '../../../stores/toast-store'
import { parseContactsText } from './constants'

export default function AudienceManagerSheet({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const qc = useQueryClient()
  const [listName, setListName] = useState('')
  const [contactsText, setContactsText] = useState('')
  const [consentConfirmed, setConsentConfirmed] = useState(false)
  const [supEmail, setSupEmail] = useState('')

  const listsQ = useQuery({ queryKey: ['uploaded-lists'], queryFn: getUploadedLists, enabled: isOpen })
  const supsQ = useQuery({ queryKey: ['suppressions'], queryFn: getSuppressions, enabled: isOpen })
  const instQ = useQuery({ queryKey: ['institution-me'], queryFn: getInstitution, enabled: isOpen })
  const lists: UploadedList[] = listsQ.data ?? []
  const sups: CampaignSuppression[] = supsQ.data ?? []
  const inst: Institution | undefined = instQ.data

  const parsed = parseContactsText(contactsText)

  const createListMut = useMutation({
    mutationFn: () =>
      createUploadedList({
        name: listName.trim(),
        source: 'csv_upload',
        source_consent_confirmed: consentConfirmed,
        contacts: parsed,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['uploaded-lists'] })
      showToast(`List added · ${parsed.length} contacts`, 'success')
      setListName('')
      setContactsText('')
      setConsentConfirmed(false)
    },
    onError: () => showToast('Could not add list', 'error'),
  })

  const delListMut = useMutation({
    mutationFn: deleteUploadedList,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['uploaded-lists'] })
      showToast('List deleted', 'success')
    },
  })

  const addSupMut = useMutation({
    mutationFn: () => addSuppression(supEmail.trim()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['suppressions'] })
      showToast('Added to suppression list', 'success')
      setSupEmail('')
    },
    onError: () => showToast('Could not add', 'error'),
  })

  const delSupMut = useMutation({
    mutationFn: deleteSuppression,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['suppressions'] })
      showToast('Removed', 'success')
    },
  })

  const approvalMut = useMutation({
    mutationFn: (v: boolean) => updateInstitution({ require_campaign_approval: v }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['institution-me'] })
      showToast('Approval setting updated', 'success')
    },
    onError: () => showToast('Could not update setting', 'error'),
  })

  return (
    <Sheet isOpen={isOpen} onClose={onClose} title="Manage audience" side="right">
      <div className="space-y-8 p-1">
        {/* Approval workflow toggle (Spec 25 §7) */}
        <section className="space-y-2">
          <h3 className="text-[13px] font-semibold text-foreground">Approval workflow</h3>
          <div className="flex items-start justify-between gap-3 rounded-lg border border-border bg-card p-3">
            <div>
              <p className="text-sm text-foreground">Require approval before sending</p>
              <p className="text-xs text-muted-foreground">
                Campaigns move to “Pending approval” and must be approved before they can be scheduled or sent.
              </p>
            </div>
            <Toggle
              label="Require campaign approval"
              checked={!!inst?.require_campaign_approval}
              onChange={(v) => approvalMut.mutate(v)}
              disabled={instQ.isLoading || approvalMut.isPending}
            />
          </div>
        </section>

        {/* Uploaded contact lists */}
        <section className="space-y-3">
          <h3 className="text-[13px] font-semibold text-foreground">Uploaded contact lists</h3>
          <div className="rounded-lg border border-border bg-card p-3 space-y-3">
            <Input label="List name" value={listName} onChange={(e) => setListName(e.target.value)} placeholder="Spring prospects" />
            <Textarea
              label="Contacts (paste CSV or one email per line)"
              value={contactsText}
              onChange={(e) => setContactsText(e.target.value)}
              rows={4}
              placeholder={'email,first_name,last_name\nana@example.com,Ana,Lee'}
            />
            <div className="flex items-center justify-between">
              <Toggle
                label="Source consent confirmed"
                checked={consentConfirmed}
                onChange={setConsentConfirmed}
                size="sm"
              />
              <span className="text-xs text-muted-foreground">{parsed.length} valid contacts detected</span>
            </div>
            <Button
              variant="secondary"
              size="sm"
              className="gap-1"
              disabled={!listName.trim() || parsed.length === 0 || createListMut.isPending}
              loading={createListMut.isPending}
              onClick={() => createListMut.mutate()}
            >
              <Upload size={14} /> Add list
            </Button>
          </div>

          {listsQ.isLoading ? (
            <Skeleton className="h-16" />
          ) : lists.length === 0 ? (
            <p className="text-xs text-muted-foreground">No uploaded lists yet.</p>
          ) : (
            <div className="space-y-2">
              {lists.map((l) => (
                <div key={l.id} className="flex items-center justify-between rounded-lg border border-border bg-card px-3 py-2">
                  <div className="min-w-0">
                    <p className="text-sm text-foreground truncate">{l.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {l.contact_count} contacts
                      {l.source_consent_confirmed && (
                        <Badge variant="success" className="ml-2">
                          consent ✓
                        </Badge>
                      )}
                    </p>
                  </div>
                  <Button variant="ghost" size="sm" className="text-destructive" onClick={() => delListMut.mutate(l.id)}>
                    <Trash2 size={14} />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Suppression list */}
        <section className="space-y-3">
          <h3 className="text-[13px] font-semibold text-foreground flex items-center gap-1.5">
            <ShieldOff size={14} className="text-muted-foreground" /> Suppression list
          </h3>
          <p className="text-xs text-muted-foreground">
            Emails here are excluded from every external send (unsubscribes land here automatically).
          </p>
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <Input label="Email" value={supEmail} onChange={(e) => setSupEmail(e.target.value)} placeholder="opted-out@example.com" />
            </div>
            <Button
              variant="tertiary"
              size="md"
              className="gap-1"
              disabled={!supEmail.includes('@') || addSupMut.isPending}
              onClick={() => addSupMut.mutate()}
            >
              <Plus size={14} /> Add
            </Button>
          </div>
          {supsQ.isLoading ? (
            <Skeleton className="h-12" />
          ) : sups.length === 0 ? (
            <p className="text-xs text-muted-foreground">No suppressed emails.</p>
          ) : (
            <div className="space-y-1.5">
              {sups.map((s) => (
                <div key={s.id} className="flex items-center justify-between rounded-md border border-border bg-card px-3 py-1.5">
                  <span className="text-[13px] text-foreground truncate">{s.email}</span>
                  <div className="flex items-center gap-2">
                    {s.reason && <Badge variant="neutral">{s.reason}</Badge>}
                    <Button variant="ghost" size="sm" className="text-destructive" onClick={() => delSupMut.mutate(s.id)}>
                      <Trash2 size={14} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </Sheet>
  )
}
