import type { Locale } from '../locales'
import { id } from './id'
import { en } from './en'
import { zhCN } from './zh-CN'

type WidenMessageLeaves<T> = {
  [K in keyof T]: T[K] extends string ? string : WidenMessageLeaves<T[K]>
}

export type Messages = WidenMessageLeaves<typeof id>

export const messages: Record<Locale, Messages> = {
  id,
  en,
  'zh-CN': zhCN,
}

