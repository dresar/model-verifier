import type { Locale } from './locales'

export function numberLocale(locale: Locale): string {
  return locale === 'en' ? 'en-US' : 'zh-CN'
}

export function formatNumber(value: number, locale: Locale): string {
  return Number.isFinite(value) ? value.toLocaleString(numberLocale(locale)) : '-'
}

export function formatDateTime(value: string | null | undefined, locale: Locale): string {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString(numberLocale(locale))
}

export function formatPercent(value: number, locale: Locale, digits = 2): string {
  return `${value.toLocaleString(numberLocale(locale), { maximumFractionDigits: digits, minimumFractionDigits: digits })}%`
}
