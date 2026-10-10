import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const read = (path) => readFileSync(resolve(root, path), 'utf8')

const files = {
  app: read('src/App.tsx'),
  client: read('src/api/client.ts'),
  zh: read('src/i18n/messages/zh-CN.ts'),
  en: read('src/i18n/messages/en.ts'),
}

const expectations = [
  ['Chinese console label exists', files.zh.includes("enterConsole: '进入控制台'")],
  ['English console label exists', files.en.includes("enterConsole: 'Open console'")],
  ['authenticated nav renders console text', files.app.includes('messages.home.enterConsole')],
  ['authenticated nav uses dashboard icon', files.app.includes('LayoutDashboard')],
  ['authenticated nav links to main console', files.app.includes("window.location.href = '/app'")],
  ['authenticated nav does not render logout confirmation', !files.app.includes('logoutConfirmTitle') && !files.app.includes('logout.mutate()')],
  ['authenticated nav does not call logout API', !files.app.includes('logoutUser')],
]

const failed = expectations.filter(([, ok]) => !ok)
if (failed.length) {
  console.error(failed.map(([name]) => `Missing: ${name}`).join('\n'))
  process.exit(1)
}

console.log('auth nav contract ok')
