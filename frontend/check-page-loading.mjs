import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { createServer } from 'vite';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

const storage = new Map([['access_token', 'access-one']]);
const redirects = [];
globalThis.window = { location: { hostname: '127.0.0.1', replace: (path) => redirects.push(path) } };
globalThis.localStorage = {
  getItem: (key) => storage.get(key) || null,
  setItem: (key, value) => storage.set(key, value), removeItem: (key) => storage.delete(key),
};
const deferred = () => {
  let resolve;
  const promise = new Promise((done) => { resolve = done; });
  return { promise, resolve };
};
const tick = () => new Promise(setImmediate);
const server = await createServer({ server: { middlewareMode: true, hmr: false }, optimizeDeps: { noDiscovery: true } });
try {
  const { apiRequest } = await server.ssrLoadModule('/shared/lib/api.js');
  const { default: Loading } = await server.ssrLoadModule('/shared/components/PageLoading.jsx');
  let calls = 0;
  const initial = deferred();
  globalThis.fetch = () => { calls++; return initial.promise; };
  const first = apiRequest('/departments/');
  const replay = apiRequest('/departments/');
  assert.equal(first, replay, 'Concurrent identical GETs must share the request');
  assert.equal(calls, 1);
  initial.resolve(Response.json([{ id: 1 }]));
  assert.deepEqual(await first, [{ id: 1 }]);
  await replay;
  globalThis.fetch = async () => { calls++; return Response.json([{ id: 2 }]); };
  assert.deepEqual(await apiRequest('/departments/'), [{ id: 2 }]);
  assert.equal(calls, 2, 'A later reload must fetch fresh data');

  calls = 0;
  const oldRead = deferred();
  globalThis.fetch = async (url, options) => {
    if (options.method === 'POST') return new Response(null, { status: 204 });
    calls++;
    return calls === 1 ? oldRead.promise : Response.json(['fresh']);
  };
  const beforeWrite = apiRequest('/after-mutation/');
  await apiRequest('/after-mutation/', { method: 'POST' });
  assert.deepEqual(await apiRequest('/after-mutation/'), ['fresh']);
  oldRead.resolve(Response.json(['old']));
  await beforeWrite;
  assert.equal(calls, 2, 'Mutation reload must not reuse a pre-mutation GET');

  calls = 0;
  const sessionRead = deferred();
  globalThis.fetch = () => { calls++; return sessionRead.promise.then(() => Response.json([])); };
  const oldSession = apiRequest('/sessions/');
  storage.set('access_token', 'access-two');
  const newSession = apiRequest('/sessions/');
  assert.equal(calls, 2, 'Different access tokens must not share data');
  sessionRead.resolve();
  await Promise.all([oldSession, newSession]);

  globalThis.fetch = async () => Response.json({ detail: 'Accès refusé' }, { status: 403 });
  await assert.rejects(apiRequest('/retry/'), (error) => error.status === 403);
  globalThis.fetch = async () => Response.json(['retry succeeded']);
  assert.deepEqual(await apiRequest('/retry/'), ['retry succeeded']);

  let refreshes = 0;
  storage.set('access_token', 'expired');
  storage.set('refresh_token', 'refresh-one');
  const refresh = deferred();
  globalThis.fetch = async (url, options) => {
    if (url.endsWith('/refresh/')) { refreshes++; return refresh.promise; }
    return options.headers.Authorization === 'Bearer expired'
      ? Response.json({ detail: 'Expired' }, { status: 401 }) : Response.json(['renewed']);
  };
  const simultaneous = [apiRequest('/roles/'), apiRequest('/permissions/')];
  await tick();
  assert.equal(refreshes, 1, 'Simultaneous expired requests must share token renewal');
  refresh.resolve(Response.json({ access: 'renewed' }));
  assert.deepEqual(await Promise.all(simultaneous), [['renewed'], ['renewed']]);

  storage.set('access_token', 'expired');
  const lateResponse = deferred();
  refreshes = 0;
  globalThis.fetch = async (url, options) => {
    if (url.endsWith('/refresh/')) { refreshes++; return Response.json({ access: 'renewed' }); }
    if (options.headers.Authorization !== 'Bearer expired') return Response.json(['renewed']);
    return url.endsWith('/late/') ? lateResponse.promise : Response.json({}, { status: 401 });
  };
  const late = apiRequest('/late/');
  await apiRequest('/early/');
  lateResponse.resolve(Response.json({}, { status: 401 }));
  await late;
  assert.equal(refreshes, 1, 'A late 401 must reuse the already renewed token');

  storage.set('access_token', 'expired-again');
  globalThis.fetch = async () => Response.json({}, { status: 401 });
  await assert.rejects(apiRequest('/expired-session/'), /session a expiré/);
  assert.equal(storage.has('access_token'), false);
  assert(redirects.includes('/pages/index.html?session=expired'));

  const markup = renderToStaticMarkup(React.createElement(Loading, { filename: 'departments.html' }));
  assert(markup.includes('role="status"'));
  assert(markup.includes('Navigation principale'));
  assert(markup.includes('<strong>Départements</strong>'));
  const assets = await readdir(new URL('./dist/assets/', import.meta.url));
  const html = await readFile(new URL('./dist/pages/departments.html', import.meta.url), 'utf8');
  const entry = html.match(/src="([^\"]+\.js)"/)[1].split('/').pop();
  const source = await readFile(new URL(`./dist/assets/${entry}`, import.meta.url), 'utf8');
  assert(Buffer.byteLength(source) < 300_000, 'Entry must stay below the previous 498 KB bundle');
  for (const prefix of ['LoginPage-', 'DepartmentsPage-', 'EmployeesPage-', 'RolesPage-', 'LeavePage-', 'EmployeeRecordsPage-', 'PayrollPage-', 'PayrollMassPage-']) {
    assert(assets.some((name) => name.startsWith(prefix)), `${prefix} must have its own page chunk`);
  }
  console.log('Chargement : GET simultanés, rechargements frais, écritures, sessions, JWT concurrent et pages séparées OK');
} finally {
  await server.close();
}
