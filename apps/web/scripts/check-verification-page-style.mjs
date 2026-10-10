import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const root = resolve(import.meta.dirname, '..')
const read = (path) => readFileSync(resolve(root, path), 'utf8')

const files = {
  page: read('src/components/ModelVerificationPage.tsx'),
  styles: read('src/styles.css'),
}

const expectations = [
  ['language switch imports homepage icon', files.page.includes('Languages')],
  ['language switch uses homepage icon size', files.page.includes('icon={<Languages size={16} />}')],
  ['verification shell top gap is compact', files.styles.includes('margin: clamp(28px, 4vh, 44px) auto 0;')],
  ['verification page defaults to GeistMono', files.styles.includes('.modelVerificationPage.modelVerificationPage :is(') && files.styles.includes('font-family: var(--font-mono);')],
  ['verification page defaults to regular weight', files.styles.includes('font-weight: 400;')],
  ['brand text is exempt from mono override', files.styles.includes('.modelVerificationPage .modelVerificationBrand,') && files.styles.includes('.modelVerificationPage .modelVerificationBrand span')],
  ['title text is exempt from mono override', files.styles.includes('.modelVerificationPage .modelVerificationHeader h1')],
]

const failed = expectations.filter(([, ok]) => !ok)
if (failed.length) {
  console.error(failed.map(([name]) => `Missing: ${name}`).join('\n'))
  process.exit(1)
}

console.log('verification page style contract ok')
