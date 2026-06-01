import "@testing-library/jest-dom";

// jsdom in Vitest 2 can expose a broken localStorage stub — provide a real
// in-memory implementation so auth-store and settings tests can import cleanly.
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

Object.defineProperty(globalThis, 'localStorage', { value: mockStorage(), writable: true })
Object.defineProperty(globalThis, 'sessionStorage', { value: mockStorage(), writable: true })
