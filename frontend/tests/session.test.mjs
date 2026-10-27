import assert from 'node:assert/strict';
import { test } from 'node:test';

const storage = new Map();
globalThis.window = { location: { hostname: 'localhost' } };
globalThis.localStorage = { getItem: (key) => storage.get(key) ?? null };
const { getUser, hasPermission } = await import('../src/shared/lib/api.js');

test('malformed session data returns an empty user without throwing', () => {
  for (const stored of ['null', '[]', '42', '"text"', '{invalid']) {
    storage.set('user', stored);
    assert.deepEqual(getUser(), {});
    assert.equal(hasPermission('paie.read'), false);
  }
});

test('only an array of explicit permission codes grants access', () => {
  for (const permissions of ['paie.read', 42, {}, null]) {
    storage.set('user', JSON.stringify({ permissions }));
    assert.equal(hasPermission('paie.read'), false);
  }
  storage.set('user', JSON.stringify({ permissions: ['paie.read'] }));
  assert.equal(hasPermission('paie.read'), true);
  assert.equal(hasPermission('paie.update'), false);
});
