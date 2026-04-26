const API_BASE = '/api/v1'

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error('Health check failed')
  return res.json()
}

export async function getCities() {
  const res = await fetch(`${API_BASE}/metadata/cities`)
  if (!res.ok) throw new Error('Failed to load cities')
  return res.json()
}

export async function getCuisines() {
  const res = await fetch(`${API_BASE}/metadata/cuisines`)
  if (!res.ok) throw new Error('Failed to load cuisines')
  return res.json()
}

export async function getRecommendations(payload) {
  const res = await fetch(`${API_BASE}/recommendations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail?.[0]?.message || 'Recommendation failed')
  }
  return res.json()
}
