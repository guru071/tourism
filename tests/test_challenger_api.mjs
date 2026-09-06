import http from 'http';
import { fetchHealth, fetchApiRoot, getApiBaseUrl, getServerRootUrl } from '../frontend/src/lib/api.ts';

async function runChallengerApiTests() {
  console.log('========================================================');
  console.log(' CHALLENGER 3: DEEP ADVERSARIAL API CLIENT STRESS TESTS');
  console.log('========================================================\n');

  let passed = 0;
  let failed = 0;

  async function withMockServer(handler, testFn) {
    const server = http.createServer((req, res) => {
      res.setHeader('Connection', 'close');
      handler(req, res);
    });
    server.keepAliveTimeout = 0;
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    const port = server.address().port;
    process.env.NEXT_PUBLIC_API_URL = `http://127.0.0.1:${port}/api/v1`;
    try {
      await testFn(port);
    } finally {
      await new Promise(resolve => server.close(resolve));
    }
  }

  // Probe 1: Root /health 404 Fallback to /api/v1/health 200
  console.log('[Probe 1] Root /health 404 Fallback to /api/v1/health 200 OK...');
  await withMockServer((req, res) => {
    if (req.url === '/health') {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ detail: 'Not Found on root' }));
    } else if (req.url === '/api/v1/health') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        status: 'ok',
        version: '1.0.0',
        services: { database: 'healthy', redis: 'healthy' }
      }));
    } else {
      res.writeHead(404);
      res.end();
    }
  }, async (port) => {
    try {
      const health = await fetchHealth();
      if (health.status === 'healthy' && health.services?.database === 'healthy') {
        console.log('  -> PASS: Dual probe successfully fell back to /api/v1/health');
        passed++;
      } else {
        console.log('  -> FAIL: Dual probe did not recover via /api/v1/health:', health);
        failed++;
      }
    } catch (err) {
      console.log('  -> FAIL: Exception during dual probe fallback:', err);
      failed++;
    }
  });

  // Probe 2: Abrupt Socket Destruction (ECONNRESET / Socket Hangup)
  console.log('\n[Probe 2] Server abruptly destroys socket during transfer...');
  await withMockServer((req, res) => {
    req.socket.destroy();
  }, async (port) => {
    try {
      const health = await fetchHealth();
      if (health.status === 'unreachable') {
        console.log('  -> PASS: Abrupt socket destruction handled gracefully as unreachable');
        passed++;
      } else {
        console.log('  -> FAIL: Expected unreachable on socket destroy, got:', health);
        failed++;
      }
    } catch (err) {
      console.log('  -> FAIL: Unhandled crash on socket destroy:', err);
      failed++;
    }
  });

  // Probe 3: HTTP 500 with plain text (non-JSON) body
  console.log('\n[Probe 3] HTTP 500 with raw text crash trace (non-JSON)...');
  await withMockServer((req, res) => {
    res.writeHead(500, { 'Content-Type': 'text/plain' });
    res.end('Traceback (most recent call last):\n  File "app/main.py", line 42\nZeroDivisionError');
  }, async (port) => {
    try {
      const health = await fetchHealth();
      if (health.status === 'error' && health.httpStatus === 500) {
        console.log('  -> PASS: Non-JSON 500 error handled gracefully without syntax crash');
        passed++;
      } else {
        console.log('  -> FAIL: Expected error with status 500, got:', health);
        failed++;
      }
    } catch (err) {
      console.log('  -> FAIL: Threw exception on non-JSON 500:', err);
      failed++;
    }
  });

  // Probe 4: HTTP 200 with HTML body (Misconfigured Reverse Proxy / Portal)
  console.log('\n[Probe 4] HTTP 200 returning HTML (e.g. captive portal or proxy error)...');
  await withMockServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end('<!DOCTYPE html><html><body>Login to Wifi</body></html>');
  }, async (port) => {
    try {
      const health = await fetchHealth();
      if (health.status === 'error') {
        console.log('  -> PASS: HTTP 200 with HTML recognized as invalid JSON / error status');
        passed++;
      } else {
        console.log('  -> FAIL: Expected error on 200 HTML, got:', health);
        failed++;
      }
    } catch (err) {
      console.log('  -> FAIL: Threw exception on 200 HTML:', err);
      failed++;
    }
  });

  // Probe 5: fetchApiRoot() under HTTP 500 and HTTP 404
  console.log('\n[Probe 5] fetchApiRoot() under HTTP 500 server error...');
  await withMockServer((req, res) => {
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Server crashed' }));
  }, async (port) => {
    try {
      const apiRoot = await fetchApiRoot();
      if (apiRoot === null) {
        console.log('  -> PASS: fetchApiRoot returned null on HTTP 500');
        passed++;
      } else {
        console.log('  -> FAIL: Expected null on 500, got:', apiRoot);
        failed++;
      }
    } catch (err) {
      console.log('  -> FAIL: Exception in fetchApiRoot on 500:', err);
      failed++;
    }
  });

  // Probe 6: Extremely Slow Server (Timeout Protection)
  console.log('\n[Probe 6] Slow Response (Exceeding Timeout Limit)...');
  await withMockServer((req, res) => {
    // Stalls indefinitely
  }, async (port) => {
    const start = Date.now();
    try {
      const health = await fetchHealth();
      const elapsed = Date.now() - start;
      console.log(`  Received response after ${elapsed}ms: status='${health.status}'`);
      if (health.status === 'unreachable' && elapsed >= 4500) {
        console.log('  -> PASS: Timeout successfully aborted stalled connection and reported unreachable');
        passed++;
      } else {
        console.log('  -> FAIL: Unexpected timeout behavior:', health, `elapsed: ${elapsed}ms`);
        failed++;
      }
    } catch (err) {
      console.log('  -> FAIL: Exception on timeout:', err);
      failed++;
    }
  });

  console.log('\n========================================================');
  console.log(` CHALLENGER API PROBE RESULTS: ${passed} PASSED, ${failed} FAILED`);
  console.log('========================================================');
  if (failed > 0) {
    process.exitCode = 1;
  }
}

runChallengerApiTests();
