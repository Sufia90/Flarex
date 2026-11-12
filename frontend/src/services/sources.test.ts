import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  listSources,
  searchSources,
  getSource,
  createSource,
  updateSource,
  deleteSource,
  setSourceVerification,
} from './sources'

const fetchMock = vi.fn()

function mockJsonResponse(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
  }
}

describe('sources service', () => {
  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('lists sources with pagination', async () => {
    const page = { total: 0, page: 1, page_size: 20, total_pages: 0, items: [] }
    fetchMock.mockResolvedValue(mockJsonResponse(page))
    const result = await listSources()
    expect(result).toEqual(page)
    const url = new URL(String(fetchMock.mock.calls[0][0]))
    expect(url.pathname).toBe('/api/v1/sources')
    expect(url.searchParams.get('page')).toBe('1')
    expect(url.searchParams.get('page_size')).toBe('20')
  })

  it('searches sources by query and status', async () => {
    const page = {
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
      items: [{ id: 'src-001', title: 'FLEX Experiment Overview' }],
    }
    fetchMock.mockResolvedValue(mockJsonResponse(page))
    const result = await searchSources({ query: 'flex', verification_status: 'confirmed' })
    expect(result.total).toBe(1)
    const url = new URL(String(fetchMock.mock.calls[0][0]))
    expect(url.pathname).toBe('/api/v1/sources/search')
    expect(url.searchParams.get('query')).toBe('flex')
    expect(url.searchParams.get('verification_status')).toBe('confirmed')
  })

  it('gets one source by id', async () => {
    const source = { id: 'src-001', title: 'FLEX Experiment Overview' }
    fetchMock.mockResolvedValue(mockJsonResponse(source))
    const result = await getSource('src-001')
    expect(result).toEqual(source)
    expect(String(fetchMock.mock.calls[0][0])).toBe('http://127.0.0.1:8000/api/v1/sources/src-001')
  })

  it('creates a source', async () => {
    const source = { id: 'src-001', title: 'FLEX Experiment Overview', verification_status: 'unverified' }
    fetchMock.mockResolvedValue(mockJsonResponse(source, 201))
    const result = await createSource({ id: 'src-001', title: 'FLEX Experiment Overview' })
    expect(result).toEqual(source)
    expect(fetchMock.mock.calls[0][1].method).toBe('POST')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      id: 'src-001',
      title: 'FLEX Experiment Overview',
    })
  })

  it('updates a source', async () => {
    const source = { id: 'src-001', title: 'Updated title' }
    fetchMock.mockResolvedValue(mockJsonResponse(source))
    const result = await updateSource('src-001', { title: 'Updated title' })
    expect(result).toEqual(source)
    expect(fetchMock.mock.calls[0][1].method).toBe('PUT')
  })

  it('deletes a source', async () => {
    fetchMock.mockResolvedValue(mockJsonResponse({ message: 'Source deleted', deleted_id: 'src-001' }))
    const result = await deleteSource('src-001')
    expect(result.deleted_id).toBe('src-001')
    expect(fetchMock.mock.calls[0][1].method).toBe('DELETE')
  })

  it('sets verification status', async () => {
    const source = { id: 'src-001', title: 'FLEX Experiment Overview', verification_status: 'verification_failed' }
    fetchMock.mockResolvedValue(mockJsonResponse(source))
    const result = await setSourceVerification('src-001', 'verification_failed')
    expect(result.verification_status).toBe('verification_failed')
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v1/sources/src-001/verification')
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ verification_status: 'verification_failed' })
  })

  it('throws an ApiError on a missing source', async () => {
    fetchMock.mockResolvedValue(mockJsonResponse({ detail: 'Source not found' }, 404))
    await expect(getSource('src-missing')).rejects.toMatchObject({ kind: 'http', status: 404 })
  })
})
