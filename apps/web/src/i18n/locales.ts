export const SUPPORTED_LOCALES = ['id', 'en', 'zh-CN'] as const
export type Locale = (typeof SUPPORTED_LOCALES)[number]
export const fallbackLocale: Locale = 'id'
export const LOCALE_STORAGE_KEY = 'model-verifier-locale'

const localeAliases: Record<string, Locale> = {
  id: 'id',
  'id-id': 'id',
  ind: 'id',
  en: 'en',
  'en-us': 'en',
  'en-gb': 'en',
  zh: 'zh-CN',
  'zh-cn': 'zh-CN',
  'zh-hans': 'zh-CN',
  'zh-sg': 'zh-CN',
}


export function isLocale(value: string | null | undefined): value is Locale {
  return Boolean(value && (SUPPORTED_LOCALES as readonly string[]).includes(value))
}

export function normalizeLocale(value: string | null | undefined): Locale | null {
  const clean = String(value || '').trim()
  if (isLocale(clean)) return clean
  const lower = clean.toLowerCase()
  if (localeAliases[lower]) return localeAliases[lower]
  if (lower.startsWith('zh-')) return 'zh-CN'
  if (lower.startsWith('en-')) return 'en'
  return null
}

export function localeFromBrowserLanguages(languages: readonly string[] | undefined): Locale | null {
  for (const item of languages || []) {
    const locale = normalizeLocale(item)
    if (locale) return locale
  }
  return null
}

export function localeFromPath(pathname: string): Locale | null {
  const first = pathname.split('/').filter(Boolean)[0]
  return normalizeLocale(first)
}

export function stripLocaleFromPath(pathname: string): string {
  const parts = pathname.split('/').filter(Boolean)
  if (parts.length && normalizeLocale(parts[0])) {
    const stripped = `/${parts.slice(1).join('/')}`
    return stripped === '/' ? '/' : stripped.replace(/\/$/u, '') || '/'
  }
  return pathname || '/'
}

export function localizedPath(path: string, _locale: Locale, search = '', hash = ''): string {
  const stripped = stripLocaleFromPath(path || '/')
  return `${stripped}${search || ''}${hash || ''}`
}

export function switchLocaleInCurrentUrl(_locale: Locale, location: Pick<Location, 'pathname' | 'search' | 'hash'> = window.location): string {
  return localizedPath(location.pathname, _locale, location.search, location.hash)
}

export function canonicalPathForCurrentUrl(location: Pick<Location, 'pathname' | 'search' | 'hash'> = window.location): string {
  return `${stripLocaleFromPath(location.pathname)}${location.search || ''}${location.hash || ''}`
}

export function readStoredLocale(storage: Storage = window.localStorage): Locale | null {
  try {
    return normalizeLocale(storage.getItem(LOCALE_STORAGE_KEY))
  } catch {
    return null
  }
}

export function writeStoredLocale(locale: Locale, storage: Storage = window.localStorage): void {
  try {
    storage.setItem(LOCALE_STORAGE_KEY, locale)
  } catch {
    // Language switching should still work when storage is blocked.
  }
}
