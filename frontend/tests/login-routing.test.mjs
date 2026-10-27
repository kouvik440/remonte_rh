import assert from 'node:assert/strict';
import { test } from 'node:test';

globalThis.localStorage = { getItem: () => null, setItem: () => {} };
const { login } = await import('../src/shared/lib/api.js');

test('login uses the frontend proxy instead of a guessed backend port', async () => {
  let requestedPath;
  globalThis.fetch = async (path) => {
    requestedPath = path;
    return { ok: false, status: 401, json: async () => ({ detail: 'Invalid credentials' }) };
  };
  await assert.rejects(login('test@example.com', 'test'), /Adresse email ou mot de passe incorrect/);
  assert.equal(requestedPath, '/api/auth/login/');
});

test('a missing login route gives a readable message without a framework traceback', async () => {
  globalThis.fetch = async () => ({ ok: false, status: 404, json: async () => ({ message: 'Not found', exception: 'Symfony', trace: [{ file: 'unrelated-project' }] }) });
  await assert.rejects(login('test@example.com', 'test'), (error) => error.status === 404 && error.message.includes('API Django') && !error.message.includes('Symfony'));
});

test('an unavailable backend gives a readable connection message', async () => {
  globalThis.fetch = async () => ({ ok: false, status: 500, json: async () => ({}) });
  await assert.rejects(login('test@example.com', 'test'), /Vérifiez que Django est démarré/);
});
