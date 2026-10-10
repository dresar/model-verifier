import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { setApiLocale } from '../api/client'
import { formatDateTime, formatNumber } from './format'
import {
  canonicalPathForCurrentUrl,
  fallbackLocale,
  localeFromBrowserLanguages,
  localeFromPath,
  localizedPath,
  readStoredLocale,
  switchLocaleInCurrentUrl,
  writeStoredLocale,
} from './locales'
import type { Locale } from './locales'
import { messages } from './messages'
import type { Messages } from './messages'
import { runtimeTranslationAttrs, translateDomToLocale } from './runtimeFallback'

type I18nContextValue = {
  locale: Locale
  messages: Messages
  setLocale: (locale: Locale) => void
  localizedPath: (path: string, search?: string, hash?: string) => string
  switchLocalePath: (locale: Locale) => string
  formatNumber: (value: number) => string
  formatDateTime: (value: string | null | undefined) => string
}

const I18nContext = createContext<I18nContextValue | null>(null)

function initialLocale(): Locale {
  return localeFromPath(window.location.pathname)
    || readStoredLocale()
    || localeFromBrowserLanguages(navigator.languages)
    || fallbackLocale
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => initialLocale())

  const setLocale = (nextLocale: Locale) => {
    setLocaleState(nextLocale)
    writeStoredLocale(nextLocale)
  }

  useEffect(() => {
    setApiLocale(locale)
    document.documentElement.lang = locale
    document.title = messages[locale].metadata.title
    const canonicalPath = canonicalPathForCurrentUrl()
    if (canonicalPath !== `${window.location.pathname}${window.location.search}${window.location.hash}`) {
      window.history.replaceState({}, '', canonicalPath)
    }
    const meta = document.querySelector<HTMLMetaElement>('meta[name="description"]')
    if (meta) meta.content = messages[locale].metadata.description
    const frame = window.requestAnimationFrame(() => translateDomToLocale(locale, document.body))
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'characterData') {
          translateDomToLocale(locale, mutation.target)
          if (mutation.target.parentElement) {
            translateDomToLocale(locale, mutation.target.parentElement)
          }
        }
        if (mutation.type === 'attributes') {
          translateDomToLocale(locale, mutation.target)
        }
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE || node.nodeType === Node.TEXT_NODE) {
            translateDomToLocale(locale, node)
          }
        })
      })
    })
    observer.observe(document.body, {
      childList: true,
      attributes: true,
      attributeFilter: [...runtimeTranslationAttrs],
      characterData: true,
      subtree: true,
    })
    return () => {
      window.cancelAnimationFrame(frame)
      observer.disconnect()
    }
  }, [locale])

  const value = useMemo<I18nContextValue>(() => ({
    locale,
    messages: messages[locale],
    setLocale,
    localizedPath: (path, search = '', hash = '') => localizedPath(path, locale, search, hash),
    switchLocalePath: (nextLocale) => switchLocaleInCurrentUrl(nextLocale),
    formatNumber: (value) => formatNumber(value, locale),
    formatDateTime: (value) => formatDateTime(value, locale),
  }), [locale])

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export function useI18n() {
  const value = useContext(I18nContext)
  if (!value) throw new Error('useI18n must be used within I18nProvider')
  return value
}
