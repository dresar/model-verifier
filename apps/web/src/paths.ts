const rawBase = import.meta.env.BASE_URL || '/'

export const verifyBasePath = rawBase.endsWith('/') ? rawBase : `${rawBase}/`

export function verifyPath(path = '') {
  const cleanPath = path.replace(/^\/+/u, '')
  return `${verifyBasePath}${cleanPath}`
}

export function verifyApiPath(path: string) {
  const cleanPath = path.startsWith('/api/') ? path.slice('/api'.length) : path.replace(/^\/+/u, '')
  return verifyPath(`api/${cleanPath.replace(/^\/+/u, '')}`)
}

export function verifyAssetPath(path: string) {
  return verifyPath(path)
}
