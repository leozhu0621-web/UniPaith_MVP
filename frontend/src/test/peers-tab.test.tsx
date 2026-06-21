import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'

import PeersTab from '../pages/student/connect/PeersTab'
import * as connectApi from '../api/connect'
import type { PeerCard, PeerVisibilityProfile } from '../api/connect'

vi.mock('../stores/toast-store', () => ({ showToast: vi.fn() }))

vi.mock('../api/connect', () => ({
  getPeersStatus: vi.fn(),
  optInPeers: vi.fn(),
  getMyPeerProfile: vi.fn(),
  updateMyPeerProfile: vi.fn(),
  discoverPeers: vi.fn(),
  requestPeer: vi.fn(),
  respondPeer: vi.fn(),
  blockPeer: vi.fn(),
  reportPeer: vi.fn(),
}))

const profile: PeerVisibilityProfile = {
  id: 'profile-1',
  display_name: 'Maya Lee',
  use_alias: false,
  intended_major: 'Computer Science',
  region: 'California, USA',
  bio: 'Building data tools for climate work.',
  share_targets: true,
  visible: true,
}

const peer: PeerCard = {
  peer_id: 'peer-1',
  display_name: 'Maya Lee',
  intended_major: 'Computer Science',
  region: 'California, USA',
  bio: 'Building data tools for climate work.',
  shared_programs: [{ id: 'program-1', name: 'MS Computer Science' }],
  connection_state: 'none',
}

function renderPeers() {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/s/posts?tab=peers']}>
        <PeersTab />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(connectApi.getPeersStatus).mockResolvedValue({ enabled: true, opted_in: false })
  vi.mocked(connectApi.optInPeers).mockResolvedValue({ opted_in: true })
  vi.mocked(connectApi.getMyPeerProfile).mockResolvedValue(profile)
  vi.mocked(connectApi.updateMyPeerProfile).mockResolvedValue(profile)
  vi.mocked(connectApi.discoverPeers).mockResolvedValue([])
  vi.mocked(connectApi.requestPeer).mockResolvedValue({})
  vi.mocked(connectApi.respondPeer).mockResolvedValue({})
  vi.mocked(connectApi.blockPeer).mockResolvedValue({})
  vi.mocked(connectApi.reportPeer).mockResolvedValue({})
})

describe('PeersTab release states', () => {
  it('renders a release-safe unavailable state when peer matching is disabled', async () => {
    vi.mocked(connectApi.getPeersStatus).mockResolvedValue({ enabled: false, opted_in: false })

    renderPeers()

    expect(await screen.findByText('Peer matching is unavailable')).toBeInTheDocument()
    expect(screen.getByText(/does not currently allow peer matching/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /open match/i })).toBeInTheDocument()
    expect(screen.queryByText(/coming soon/i)).not.toBeInTheDocument()
  })

  it('keeps the opt-in state concrete and saves the preference', async () => {
    renderPeers()

    expect(await screen.findByText('Connect with other applicants')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /turn on peers/i }))

    await waitFor(() => {
      expect(connectApi.optInPeers).toHaveBeenCalledWith(true)
    })
  })

  it('renders an actionable empty state for opted-in students with no peers', async () => {
    vi.mocked(connectApi.getPeersStatus).mockResolvedValue({ enabled: true, opted_in: true })
    vi.mocked(connectApi.discoverPeers).mockResolvedValue([])

    renderPeers()

    expect(await screen.findByText('No peers yet for your programs')).toBeInTheDocument()
    expect(screen.getByText(/share programs with your saved or followed schools/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /open match/i })).toBeInTheDocument()
  })

  it('labels peer card controls and exposes privacy toggles as switches', async () => {
    vi.mocked(connectApi.getPeersStatus).mockResolvedValue({ enabled: true, opted_in: true })
    vi.mocked(connectApi.discoverPeers).mockResolvedValue([peer])

    renderPeers()

    expect(await screen.findByText('Maya Lee')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Report Maya Lee' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Block Maya Lee' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /visibility settings/i }))

    expect(await screen.findByRole('switch', { name: /discoverable/i })).toHaveAttribute('aria-checked', 'true')
    expect(screen.getByRole('switch', { name: /show my target programs/i })).toHaveAttribute('aria-checked', 'true')
  })
})
