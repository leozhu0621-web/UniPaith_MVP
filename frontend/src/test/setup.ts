import "@testing-library/jest-dom";

import apiClient from "../api/client";

// Tests must mock their own API modules. Any unmocked call rejects immediately
// here instead of hitting a real server or going through jsdom's slow XHR path
// (which, on a backend-less CI runner, fails asynchronously and can leak a
// render past the test that raised it). This mirrors CI — there is no backend —
// while keeping the failure synchronous and self-contained.
apiClient.defaults.adapter = () =>
  Promise.reject(new Error("Unmocked API call in test (mock the api module)"));

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
