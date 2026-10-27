import assert from 'node:assert/strict';
import { createServer } from 'vite';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

globalThis.window = { location: { hostname: '127.0.0.1', pathname: '/pages/leaves.html' } };
globalThis.localStorage = {
  getItem(key) {
    if (key === 'access_token') return 'test-token';
    if (key === 'user') return JSON.stringify({ id: 1, email: 'test@example.com', permissions: ['demande_absence.read'] });
    return null;
  },
};
for (const tab of ['requests', 'planning']) {
  const server = await createServer({
    server: { middlewareMode: true },
    plugins: [{
      name: 'select-tab-for-render-check',
      enforce: 'pre',
      transform(code, id) {
        if (!id.endsWith('/LeavePage.jsx')) return;
        return code.replace(/const \[activeTab, setActiveTab\] = useState\([\s\S]*?: 'types'\);/, `const [activeTab, setActiveTab] = useState('${tab}');`);
      },
    }],
  });
  try {
    const { default: LeavePage } = await server.ssrLoadModule('/modules/module-2/pages/LeavePage.jsx');
    const html = renderToStaticMarkup(React.createElement(LeavePage));
    assert.equal(html.includes('<h2>Planning d'), tab === 'planning');
    assert.equal(html.includes('<h2>Mes demandes</h2>'), tab === 'requests');
    console.log(`${tab}: render OK, correct section`);
  } finally {
    await server.close();
  }
}
