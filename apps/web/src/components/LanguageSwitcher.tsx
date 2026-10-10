import type { ReactNode } from 'react'

import { useI18n } from '../i18n/I18nProvider'

export function LanguageSwitcher({
  className = '',
  icon = null,
  labelClassName = '',
}: {
  className?: string
  icon?: ReactNode
  labelClassName?: string
}) {
  const { locale, setLocale, messages } = useI18n()
  const nextLocale = locale === 'id' ? 'en' : 'id'
  const label = locale === 'id' ? 'ID' : 'EN'
  return (
    <button
      className={className || 'languageSwitch'}
      type="button"
      onClick={() => setLocale(nextLocale)}
      title={messages.common.language}
      aria-label={messages.common.language}
    >
      {icon}
      <span className={labelClassName}>{label}</span>
    </button>
  )

}
