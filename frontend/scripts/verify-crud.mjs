const baseUrl = process.env.CRUD_BASE_URL ?? 'http://127.0.0.1:8001'
const apiPrefix = process.env.CRUD_API_PREFIX ?? '/api'

let passed = 0
let failed = 0
const failures = []

async function request(method, path, body) {
  const response = await fetch(`${baseUrl}${apiPrefix}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  let data = null
  try {
    data = await response.json()
  } catch {
    data = null
  }
  return { status: response.status, data }
}

async function check(name, method, path, body, expectStatus, verify) {
  try {
    const { status, data } = await request(method, path, body)
    if (status !== expectStatus) {
      throw new Error(`expected ${expectStatus}, got ${status} (${JSON.stringify(data)})`)
    }
    if (verify) {
      verify(data)
    }
    passed += 1
    console.log(`PASS ${name}`)
  } catch (error) {
    failed += 1
    failures.push(name)
    console.log(`FAIL ${name}: ${error.message}`)
  }
}

function expectField(data, field, value) {
  if (data[field] !== value) {
    throw new Error(`expected ${field} to be ${JSON.stringify(value)}, got ${JSON.stringify(data[field])}`)
  }
}

const expId = 'crud-exp-001'
const hwId = 'crud-hw-001'
const relId = 'crud-rel-001'
const srcId = 'crud-src-001'

await check('health', 'GET', '/health', undefined, 200, (data) => expectField(data, 'status', 'ok'))

await check('create experiment', 'POST', '/v1/experiments', { id: expId, name: 'CRUD test experiment' }, 201, (data) => expectField(data, 'id', expId))
await check('create hardware', 'POST', '/v1/hardware', { id: hwId, name: 'CRUD test hardware', hardware_type: 'apparatus' }, 201, (data) => expectField(data, 'id', hwId))
await check('create source', 'POST', '/v1/sources', { id: srcId, title: 'CRUD test source' }, 201, (data) => expectField(data, 'verification_status', 'unverified'))
await check('create relationship', 'POST', '/v1/relationships', { id: relId, experiment_id: expId, hardware_id: hwId, relationship_type: 'used_in' }, 201, (data) => expectField(data, 'id', relId))

await check('search finds the experiment', 'GET', '/v1/experiments/search?query=crud', undefined, 200, (data) => {
  if (!data.items.some((item) => item.id === expId)) {
    throw new Error('created experiment not in search results')
  }
})

await check('get experiment', 'GET', `/v1/experiments/${expId}`, undefined, 200, (data) => expectField(data, 'name', 'CRUD test experiment'))
await check('get hardware', 'GET', `/v1/hardware/${hwId}`, undefined, 200, (data) => expectField(data, 'name', 'CRUD test hardware'))
await check('get source', 'GET', `/v1/sources/${srcId}`, undefined, 200, (data) => expectField(data, 'title', 'CRUD test source'))
await check('get relationship', 'GET', `/v1/relationships/${relId}`, undefined, 200, (data) => expectField(data, 'relationship_type', 'used_in'))

await check('update experiment', 'PUT', `/v1/experiments/${expId}`, { id: expId, name: 'CRUD test experiment updated' }, 200, (data) => expectField(data, 'name', 'CRUD test experiment updated'))
await check('update hardware', 'PUT', `/v1/hardware/${hwId}`, { id: hwId, name: 'CRUD test hardware updated', hardware_type: 'apparatus' }, 200, (data) => expectField(data, 'name', 'CRUD test hardware updated'))
await check('update source', 'PUT', `/v1/sources/${srcId}`, { id: srcId, title: 'CRUD test source updated' }, 200, (data) => expectField(data, 'title', 'CRUD test source updated'))
await check('update relationship', 'PUT', `/v1/relationships/${relId}`, { id: relId, experiment_id: expId, hardware_id: hwId, relationship_type: 'used_in', role: 'housing' }, 200, (data) => expectField(data, 'role', 'housing'))

await check('get updated experiment', 'GET', `/v1/experiments/${expId}`, undefined, 200, (data) => expectField(data, 'name', 'CRUD test experiment updated'))

await check('set source verification', 'POST', `/v1/sources/${srcId}/verification`, { verification_status: 'confirmed' }, 200, (data) => expectField(data, 'verification_status', 'confirmed'))

await check('delete experiment blocked while linked', 'DELETE', `/v1/experiments/${expId}`, undefined, 409)
await check('delete relationship', 'DELETE', `/v1/relationships/${relId}`, undefined, 200)
await check('get deleted relationship', 'GET', `/v1/relationships/${relId}`, undefined, 404)
await check('delete experiment', 'DELETE', `/v1/experiments/${expId}`, undefined, 200)
await check('get deleted experiment', 'GET', `/v1/experiments/${expId}`, undefined, 404)
await check('delete hardware', 'DELETE', `/v1/hardware/${hwId}`, undefined, 200)
await check('get deleted hardware', 'GET', `/v1/hardware/${hwId}`, undefined, 404)
await check('delete source', 'DELETE', `/v1/sources/${srcId}`, undefined, 200)
await check('get deleted source', 'GET', `/v1/sources/${srcId}`, undefined, 404)

console.log(`\n${passed} passed, ${failed} failed`)
if (failed > 0) {
  console.log(`Failed checks: ${failures.join(', ')}`)
  process.exit(1)
}
