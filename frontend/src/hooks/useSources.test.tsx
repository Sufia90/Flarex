import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { act, renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useDeleteSource, useSetSourceVerification, useSource, useSources } from './useSources'
import type { Source } from '../types'

const fetchMock = vi.fn()

function mockJsonResponse(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  }
}

function createWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return function Wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  }
}

describe('useSources hooks', () => {
  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads the source list', async () => {
    const page = {
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
      items: [{ id: 'src-001', title: 'FLEX Experiment Overview' }],
    }
    fetchMock.mockResolvedValue(mockJsonResponse(page))
    const { result } = renderHook(() => useSources(), { wrapper: createWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.items[0].id).toBe('src-001')
  })

  it('loads one source', async () => {
    const source = { id: 'src-001', title: 'FLEX Experiment Overview' }
    fetchMock.mockResolvedValue(mockJsonResponse(source))
    const { result } = renderHook(() => useSource('src-001'), { wrapper: createWrapper() })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data?.title).toBe('FLEX Experiment Overview')
  })

  it('sets verification status through the mutation', async () => {
    const source = { id: 'src-001', title: 'FLEX Experiment Overview', verification_status: 'confirmed' }
    fetchMock.mockResolvedValue(mockJsonResponse(source))
    const { result } = renderHook(() => useSetSourceVerification(), { wrapper: createWrapper() })
    let updated: Source | undefined
    await act(async () => {
      updated = await result.current.mutateAsync({ sourceId: 'src-001', verificationStatus: 'confirmed' })
    })
    expect(updated?.verification_status).toBe('confirmed')
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v1/sources/src-001/verification')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ verification_status: 'confirmed' })
  })

  it('deletes a source through the mutation', async () => {
    fetchMock.mockResolvedValue(mockJsonResponse({ message: 'Source deleted', deleted_id: 'src-001' }))
    const { result } = renderHook(() => useDeleteSource(), { wrapper: createWrapper() })
    let deleted: void | undefined
    await act(async () => {
      deleted = await result.current.mutateAsync('src-001')
    })
    expect(deleted).toBeUndefined()
    expect(fetchMock.mock.calls[0][1].method).toBe('DELETE')
  })
})
