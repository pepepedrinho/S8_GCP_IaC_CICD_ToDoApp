const { test, before, after } = require('node:test');
const assert = require('node:assert/strict');
const { createApp } = require('../src/app');
let server, url;
before(async () => {
  server = createApp({ Todo: {}, checkDatabase: async () => { throw new Error('private secret'); } }).listen(0);
  await new Promise(resolve => server.once('listening', resolve));
  url = `http://127.0.0.1:${server.address().port}`;
});
after(() => new Promise(resolve => server.close(resolve)));
test('database failure affects readiness only and never exposes the error', async () => {
  const r = await fetch(url + '/health/ready');
  assert.equal(r.status, 503); assert.equal((await r.text()).includes('secret'), false);
  assert.equal((await fetch(url + '/health/live')).status, 200);
});
test('invalid task values are rejected before database access', async () => {
  for (const text of ['', '  ', 123, 'x'.repeat(501)]) {
    const r = await fetch(url + '/todos', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) });
    assert.equal(r.status, 400);
  }
});
test('invalid identifiers return 400, unmatched routes 404; no open CORS', async () => {
  const r = await fetch(url + '/todos/invalid', { method: 'PATCH' });
  assert.equal(r.status, 400); assert.equal(r.headers.get('access-control-allow-origin'), null);
  assert.equal((await fetch(url + '/missing')).status, 404);
});
