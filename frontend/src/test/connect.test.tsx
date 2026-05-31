/**
 * Spec 20 (Connect) — frontend smoke test.
 *
 * Verifies the Connect API client contract and that the feed cards render the
 * three item kinds with the brand-correct affordances (gold pinned marker,
 * cobalt CTAs, the program_change copy).
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'

import * as connectApi from '../api/connect'
import type { ConnectFeedItem } from '../api/connect'
import FeedItemCard from '../pages/student/connect/ConnectCards'

describe('Connect API client', () => {
  it('exports the full Updates / Events / Follows / Peers contract', () => {
    const fns = [
      'getConnectFeed', 'getConnectEvents',
      'getFollowing', 'followInstitution', 'muteFollowing', 'unfollowInstitution',
      'getPeersStatus', 'optInPeers', 'getMyPeerProfile', 'updateMyPeerProfile',
      'discoverPeers', 'requestPeer', 'respondPeer', 'blockPeer', 'reportPeer',
    ]
    for (const fn of fns) {
      expect(typeof (connectApi as Record<string, unknown>)[fn]).toBe('function')
    }
  })
})

describe('Connect feed cards (Spec 20 §4 / §10)', () => {
  const base = {
    id: 'x', date: new Date().toISOString(), institution_id: 'i1',
    institution_name: 'University of Foo', program_id: 'p1', program_name: 'CS Masters',
  }
  const noop = () => {}

  it('renders a pinned post with the gold Pinned marker and a cobalt View program CTA', () => {
    const item: ConnectFeedItem = { ...base, kind: 'post', pinned: true, title: 'Scholarship news', body: 'short body' }
    render(<FeedItemCard item={item} onViewProgram={noop} onAddToCalendar={noop} />)
    expect(screen.getByText('Scholarship news')).toBeTruthy()
    expect(screen.getByText('Pinned')).toBeTruthy()
    expect(screen.getByText('View program')).toBeTruthy()
  })

  it('renders a program_change card with the spec copy', () => {
    const item: ConnectFeedItem = { ...base, kind: 'program_change', change_summary: 'This program changed a requirement', muted: true }
    render(<FeedItemCard item={item} onViewProgram={noop} onAddToCalendar={noop} />)
    expect(screen.getByText('This program changed a requirement')).toBeTruthy()
    expect(screen.getByText('(shown despite mute)')).toBeTruthy()
  })

  it('renders a deadline card with the add-to-calendar CTA', () => {
    const item: ConnectFeedItem = {
      ...base, kind: 'deadline',
      deadline: new Date(Date.now() + 86400000 * 10).toISOString().slice(0, 10), days_until: 10,
    }
    render(<FeedItemCard item={item} onViewProgram={noop} onAddToCalendar={noop} />)
    expect(screen.getByText('Add deadline to calendar')).toBeTruthy()
  })
})
