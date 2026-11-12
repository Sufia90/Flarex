const baseUrl = process.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const apiPrefix = process.env.VITE_API_PREFIX || '/api'
const apiBase = `${baseUrl.replace(/\/$/, '')}${apiPrefix}`
const timeoutMs = Number(process.env.VITE_API_TIMEOUT_MS || 10000)

let passed = 0
let failed = 0
const failures = []

async function check(name, path, options = {}, expectStatus = 200, expectJson = true) {
  const url = `${apiBase}${path}`
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(url, { ...options, signal: controller.signal })
    const text = await response.text()
    let body = null
    try {
      body = JSON.parse(text)
    } catch {
      body = null
    }
    const ok = response.status === expectStatus && (!expectJson || body !== null)
    if (ok) {
      passed += 1
      console.log(`PASS ${name} ${response.status} ${path}`)
    } else {
      failed += 1
      failures.push(name)
      console.log(`FAIL ${name} ${response.status} ${path}`)
    }
  } catch (error) {
    failed += 1
    failures.push(name)
    console.log(`FAIL ${name} ${error.message} ${path}`)
  } finally {
    clearTimeout(timer)
  }
}

async function main() {
  await check('health', '/health')
  await check('experiments list', '/v1/experiments')
  await check('experiments search', '/v1/experiments/search')
  await check('hardware list', '/v1/hardware')
  await check('hardware search', '/v1/hardware/search')
  await check('relationships list', '/v1/relationships')
  await check('relationships search', '/v1/relationships/search')
  await check('fire-safety insights', '/v1/fire-safety/insights')
  await check('fire-safety summary', '/v1/fire-safety/summary')
  await check('fire-safety prevention', '/v1/fire-safety/prevention')
  await check('fire-safety detection', '/v1/fire-safety/detection')
  await check('fire-safety suppression', '/v1/fire-safety/suppression')
  await check('comparison experiments missing records', '/v1/comparisons/experiments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ experiment_ids: ['exp-001', 'exp-002'] }),
  }, 404)
  await check('ranking empty dataset', '/v1/rankings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ criterion: 'experiment_documentation_completeness' }),
  })
  await check('mission relevance experiment missing record', '/v1/mission-relevance/experiments/exp-001?mission=ISS', {}, 404)
  await check('mission relevance hardware missing record', '/v1/mission-relevance/hardware/hw-001?mission=ISS', {}, 404)
  await check('invalid endpoint', '/v1/does-not-exist', {}, 404)
  await check('CORS preflight', '/v1/experiments', {
    method: 'OPTIONS',
    headers: {
      Origin: 'http://localhost:5173',
      'Access-Control-Request-Method': 'GET',
    },
  }, 200, false)
  console.log(`\n${passed} passed, ${failed} failed`)
  if (failed > 0) {
    console.log(`Failed checks: ${failures.join(', ')}`)
    process.exitCode = 1
  }
}

await main()
