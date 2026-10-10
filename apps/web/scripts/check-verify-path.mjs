import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const read = (path) => readFileSync(resolve(root, path), 'utf8')

const files = {
  vite: read('vite.config.ts'),
  client: read('src/api/client.ts'),
  app: read('src/App.tsx'),
  page: read('src/components/ModelVerificationPage.tsx'),
  html: read('index.html'),
  css: read('src/styles.css'),
}

const expectations = [
  ['Vite base is /verify/', files.vite.includes("base: '/verify/'")],
  ['dev server redirects /verify to /verify/', files.vite.includes("req.url === '/verify'") && files.vite.includes("res.setHeader('Location', '/verify/')")],
  ['dev proxy accepts /verify/api', files.vite.includes("'/verify/api'")],
  ['API client builds verify-prefixed API paths', files.client.includes('verifyApiPath')],
  ['login redirects use verify-prefixed API paths', files.app.includes('verifyApiPath(`/api/auth/github')],
  ['login next path returns to /verify/', files.app.includes('verifyPath(\'/\')')],
  ['brand asset uses verify asset helper', files.page.includes('verifyAssetPath')],
  ['HTML public assets use Vite public-root paths', files.html.includes('href="/brand/logo.svg')],
  ['font URLs use Vite public-root paths', files.css.includes('url("/fonts/azeret-500.woff2")')],
]

const failed = expectations.filter(([, ok]) => !ok)
if (failed.length) {
  console.error(failed.map(([name]) => `Missing: ${name}`).join('\n'))
  process.exit(1)
}

console.log('verify path contract ok')
