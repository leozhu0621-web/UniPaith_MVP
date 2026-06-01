import "@testing-library/jest-dom";

function mockStorage(): Storage {
  const store = new Map<string, string>()
  return {
    get length() { return store.size },
    clear: () => store.clear(),
    getItem: (key: string) => (store.has(key) ? store.get(key)! : null),
    key: (index: number) => Array.from(store.keys())[index] ?? null,
    removeItem: (key: string) => { store.delete(key) },
    setItem: (key: string, value: string) => { store.set(key, String(value)) },
  }
}

function installStorage() {
  const ls = mockStorage()
  const ss = mockStorage()
  for (const target of [globalThis, typeof window !== 'undefined' ? window : null]) {
    if (!target) continue
    Object.defineProperty(target, 'localStorage', { value: ls, writable: true, configurable: true })
    Object.defineProperty(target, 'sessionStorage', { value: ss, writable: true, configurable: true })
  }
}
installStorage()
