import { verifyApiPath } from '../paths'

export type Principal =
  | { authenticated: false; kind: null; user: null }
  | { authenticated: true; kind: 'admin'; user: { username: string } }
  | {
      authenticated: true
      kind: 'user'
      user: {
        id: number
        github_login: string
        name: string
        avatar_url: string
        status_slug: string
        preferred_locale: string
        login_methods: string[]
      }
    }

export type SiteApiKey = {
  id: number
  api_key_masked: string
  enabled: boolean
  last_sync_at: string | null
  last_sync_error: string
}

export type Site = {
  id: number
  name: string
  base_url: string
  api_key_count: number
  api_keys: SiteApiKey[]
  note: string
  enabled: boolean
  last_sync_at: string | null
  last_sync_error: string
}

export type RegistryModelSummary = {
  registry_id: string
  name: string
  author: string
  author_id: string
  author_label?: string
  context_length: number | null
  max_input_tokens: number | null
  max_output_tokens: number | null
  reasoning: boolean | null
  tool_calling: boolean | null
  modalities: string[]
}

export type SiteModelPrice = {
  source: string
  project_group_name: string
  project_input_price: string
  project_output_price: string
  project_group_ratio: string
  reference_input_price: string
  reference_output_price: string
  project_price_summary: string
  project_discount_summary: string
  reference_price_summary: string
  synced_at: string | null
  sync_error: string
}

export type ModelRow = {
  id: number
  site_id: number
  site_name: string
  site_base_url: string
  site_api_key_id: number
  api_key_masked: string
  model: string
  probe_enabled: boolean
  probe_stream_mode: 'auto' | 'stream' | 'non_stream'
  status: string
  latency_ms: number | null
  first_chunk_ms: number | null
  recent_success_rate: number | null
  last_error: string
  checked_at: string | null
  recent_probe_results: boolean[]
  registry_match?: RegistryModelSummary | null
  price?: SiteModelPrice | null
}

export type ModelVerificationProviderMode = 'auto' | 'openai' | 'anthropic'

export type ModelVerificationStepTokenEstimate = {
  id: string
  call_count: number
  estimated_input_tokens: number
  max_output_tokens: number
}

export type ModelVerificationTokenEstimate = {
  disclaimer: string
  case_count: number
  call_count: number
  estimated_input_tokens: number
  max_output_tokens: number
  steps: ModelVerificationStepTokenEstimate[]
}

export type ModelVerificationSettings = {
  quota_cost: number
  daily_limit: number
  anonymous_daily_limit: number
  authenticated: boolean
  token_estimate: ModelVerificationTokenEstimate
}

export type ModelVerificationIdentityEcho = {
  category: string
  label: string
  claimed_provider: string
  claimed_provider_label: string
  observed_provider: string
  observed_provider_label: string
  matched_aliases: string[]
  disclaimer: string
}

export type ModelVerificationIdentityEchoSummary = {
  status: string
  label: string
  disclaimer: string
  total_cases: number
  self_count: number
  cross_provider_count: number
  refusal_count: number
  unknown_count: number
  claimed_provider: string
  claimed_provider_label: string
  observed_providers: { provider: string; label: string; count: number }[]
}

export type ModelVerificationCapabilityProfile = {
  id: string
  label: string
  description: string
  required_dimensions: string[]
  minimum_identity_score: number
  minimum_dimension_scores: Record<string, number>
  dimension_weights: Record<string, number>
  probe_case_ids: string[]
  requires_fingerprint: boolean
  match_rule?: {
    profile_id: string
    provider: string
    match_type: string
    pattern: string
    label: string
    priority: number
  } | null
}

export type ModelVerificationProfileAssessment = {
  status: string
  reason: string
  missing_dimensions: string[]
  weak_dimensions: { dimension: string; score: number; minimum: number }[]
  minimum_identity_score: number
  dimension_weights: Record<string, number>
  weighted_identity_score: number
}

export type ModelVerificationCase = {
  id: string
  title: string
  dimension: string
  evidence_role: string
  status: string
  score: number
  latency_ms: number
  signals: string[]
  matched?: string[]
  missing?: string[]
  forbidden?: string[]
  reason?: string
  expected_criteria?: string[]
  identity_echo?: ModelVerificationIdentityEcho | null
  prompt: string
  answer_preview: string
  error: string
}

export type ModelVerificationReport = {
  claimed_model: string
  claimed_model_verified: boolean
  registry_match?: RegistryModelSummary | null
  capability_profile?: ModelVerificationCapabilityProfile | null
  profile_assessment?: ModelVerificationProfileAssessment | null
  actual_model: string
  upstream_model: string
  source: 'saved' | 'temporary'
  base_url: string
  site_name: string
  api_key_masked: string
  quota_cost: number
  risk_level: string
  conclusion: string
  identity_score: number
  dimension_scores: Record<string, number>
  signals: string[]
  recommendations: string[]
  identity_echo_summary?: ModelVerificationIdentityEchoSummary | null
  verdict: 'verified' | 'compatible' | 'suspicious' | 'substituted' | 'unreachable'
  confidence_score: number
  provider_guess: string
  protocol_score: number
  capability_score: number
  usage_score: number
  protocol_evidence: Record<string, unknown>
  usage_evidence: Record<string, unknown>
  risk_signals: string[]
  cases: ModelVerificationCase[]
}

export type ModelVerificationTemporaryModels = {
  base_url: string
  api_key_masked: string
  items: string[]
}

export type ModelVerificationRunPayload =
  | { source?: 'saved'; site_model_id: number; claimed_model: string; provider_mode?: ModelVerificationProviderMode }
  | { source: 'temporary'; base_url: string; api_key: string; claimed_model: string; provider_mode?: ModelVerificationProviderMode }

type ModelVerificationRunJob = {
  job_id: string
  status: 'running'
}

let apiLocale = 'id'


export function setApiLocale(locale: string) {
  apiLocale = locale
}

async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { data } = await apiResponse<T>(path, init)
  return data
}

async function apiResponse<T>(path: string, init: RequestInit = {}): Promise<{ data: T; status: number }> {
  const response = await fetch(verifyApiPath(path), {
    credentials: 'include',
    ...init,
    headers: {
      'Content-Type': 'application/json',
      'X-Locale': apiLocale,
      ...(init.headers || {}),
    },
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const message = data && typeof data === 'object' && 'error' in data
      ? String(data.error)
      : data && typeof data === 'object' && 'detail' in data
        ? String(data.detail)
        : `HTTP ${response.status}`
    throw new Error(message)
  }
  return { data: data as T, status: response.status }
}

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

export const getSites = () => api<{ items: Site[] }>('/api/sites')
export const getModels = () => api<{ items: ModelRow[] }>('/api/models')
export const getMe = (scope: 'user' | 'admin' = 'user') => api<Principal>(`/api/me?scope=${scope}`)

export function requestEmailLoginCode(email: string) {
  return api<{ ok: boolean }>('/api/auth/email/request-code', {
    method: 'POST',
    body: JSON.stringify({ email }),
  })
}

export function verifyEmailLoginCode(email: string, code: string) {
  return api<{ ok: boolean }>('/api/auth/email/verify-code', {
    method: 'POST',
    body: JSON.stringify({ email, code }),
  })
}

export function logoutUser() {
  return api<{ ok: boolean }>('/api/auth/logout?scope=user', {
    method: 'POST',
  })
}

export const getModelVerificationSettings = (claimedModel?: string) => (
  api<ModelVerificationSettings>(`/api/model-verification/settings?claimed_model=${encodeURIComponent(claimedModel || '')}`)
)

export const getTemporaryModelVerificationModels = (payload: { base_url: string; api_key: string }) => (
  api<ModelVerificationTemporaryModels>('/api/model-verification/temporary-models', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
)

export async function createModelVerificationRun(payload: ModelVerificationRunPayload): Promise<ModelVerificationReport> {
  const started = await apiResponse<ModelVerificationReport | ModelVerificationRunJob>('/api/model-verification/runs', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

  if (started.status !== 202 || !started.data || typeof started.data !== 'object' || !('job_id' in started.data)) {
    return started.data as ModelVerificationReport
  }

  const jobId = started.data.job_id
  for (;;) {
    await sleep(2000)
    const next = await apiResponse<ModelVerificationReport | ModelVerificationRunJob>(`/api/model-verification/runs/${encodeURIComponent(jobId)}`)
    if (next.status !== 202 || !next.data || typeof next.data !== 'object' || !('job_id' in next.data)) {
      return next.data as ModelVerificationReport
    }
  }
}
