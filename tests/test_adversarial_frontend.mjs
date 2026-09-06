import http from 'http';
import { fetchHealth, fetchApiRoot, getApiBaseUrl, getServerRootUrl } from '../frontend/src/lib/api.ts';

async function runTests() {
  console.log('========================================================');
  console.log(' ADVERSARIAL TEST SUITE: FRONTEND API CLIENT ROBUSTNESS');
  console.log('========================================================\n');

  let passed = 0;
  let failed = 0;

  // Test 1: Backend Totally Offline
  console.log('[Test 1] Backend Totally Offline (Port 9999)...');
  process.env.NEXT_PUBLIC_API_URL = 'http://127.0.0.1:9999/api/v1';
  try {
    const health = await fetchHealth();
    if (health.status === 'unreachable' && health.message && health.timestamp) {
      console.log('  -> PASS: Gracefully returned unreachable object:', health);
      passed++;
    } else {
      console.log('  -> FAIL: Unexpected response shape:', health);
      failed++;
    }
  } catch (err) {
    console.log('  -> FAIL: Threw unhandled exception:', err);
    failed++;
  }

  try {
    const apiRoot = await fetchApiRoot();
    if (apiRoot === null) {
      console.log('  -> PASS: fetchApiRoot returned null gracefully');
      passed++;
    } else {
      console.log('  -> FAIL: Expected null, got:', apiRoot);
      failed++;
    }
  } catch (err) {
    console.log('  -> FAIL: Threw unhandled exception in fetchApiRoot:', err);
    failed++;
  }

  // Helper to run ephemeral mock server with keep-alive disabled
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

  // Test 2: HTTP 500 Internal Server Error
  console.log('\n[Test 2] Backend Returns 500 Internal Server Error...');
  await withMockServer((req, res) => {
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ detail: 'Internal Server Error' }));
  }, async (port) => {
    try {
      const health = await fetchHealth();
      if (['error', 'degraded', 'unreachable'].includes(health.status)) {
        console.log(`  -> PASS: Handled 500 gracefully with status '${health.status}'`);
        passed++;
      } else {
        console.log('  -> FAIL: Unexpected status on 500:', health);
        failed++;
      }
    } catch (err) {
      console.log('  -> FAIL: Threw on 500:', err);
      failed++;
    }
  });

  // Test 3: HTTP 502 Bad Gateway with HTML error body
  console.log('\n[Test 3] Backend Returns 502 with HTML payload...');
  await withMockServer((req, res) => {
    res.writeHead(502, { 'Content-Type': 'text/html' });
    res.end('<html><head><title>502 Bad Gateway</title></head><body>502 Bad Gateway</body></html>');
  }, async (port) => {
    try {
      const health = await fetchHealth();
      if (['error', 'degraded', 'unreachable'].includes(health.status)) {
        console.log(`  -> PASS: Handled 502 HTML gracefully with status '${health.status}'`);
        passed++;
      } else {
        console.log('  -> FAIL: Unexpected status on 502 HTML:', health);
        failed++;
      }
    } catch (err) {
      console.log('  -> FAIL: Threw on 502 HTML:', err);
      failed++;
    }
  });

  // Test 4: HTTP 200 with malformed JSON
  console.log('\n[Test 4] Backend Returns 200 OK with Malformed / Truncated JSON...');
  await withMockServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end('{"status": "ok", "unclosed_json:');
  }, async (port) => {
    try {
      const health = await fetchHealth();
      if (['error', 'degraded', 'unreachable'].includes(health.status)) {
        console.log(`  -> PASS: Handled SyntaxError in JSON body gracefully with status '${health.status}'`);
        passed++;
      } else {
        console.log('  -> FAIL: Expected unreachable/error fallback on JSON SyntaxError, got:', health);
        failed++;
      }
    } catch (err) {
      console.log('  -> FAIL: Threw on JSON SyntaxError:', err);
      failed++;
    }
  });

  // Test 5: HTTP 200 with anomalous / partial JSON fields
  console.log('\n[Test 5] Backend Returns 200 OK with Missing Fields...');
  await withMockServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ custom_field: 123 }));
  }, async (port) => {
    try {
      const health = await fetchHealth();
      if (health.status && health.timestamp) {
        console.log('  -> PASS: Did not crash on empty fields (defaulted status: ' + health.status + ')');
        passed++;
      } else {
        console.log('  -> FAIL: Broken health object:', health);
        failed++;
      }
    } catch (err) {
      console.log('  -> FAIL: Threw on missing fields:', err);
      failed++;
    }
  });

  // Test 6: URL derivation edge cases
  console.log('\n[Test 6] URL derivation edge cases...');
  process.env.NEXT_PUBLIC_API_URL = '  http://custom-host:9000/api/v1/  ';
  const derivedBase = getApiBaseUrl();
  const derivedRoot = getServerRootUrl();
  console.log('  Trimmed Base URL:', derivedBase);
  console.log('  Derived Root URL:', derivedRoot);
  if (derivedBase === 'http://custom-host:9000/api/v1' && derivedRoot === 'http://custom-host:9000') {
    console.log('  -> PASS: Cleanly stripped whitespace and trailing slashes');
    passed++;
  } else {
    console.log('  -> FAIL: Incorrect URL normalization');
    failed++;
  }

  // Test 7: Degraded Backend HTTP 503 with Structured Services
  console.log('\n[Test 7] Backend Returns 503 Degraded with Service Telemetry...');
  await withMockServer((req, res) => {
    res.writeHead(503, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      status: 'degraded',
      services: { database: 'unreachable', redis: 'healthy' },
    }));
  }, async (port) => {
    try {
      const health = await fetchHealth();
      if (health.status === 'degraded' && health.services?.database === 'unreachable' && health.services?.redis === 'healthy') {
        console.log('  -> PASS: Correctly preserved degraded telemetry from 503 payload');
        passed++;
      } else {
        console.log('  -> FAIL: Expected degraded with services, got:', health);
        failed++;
      }
    } catch (err) {
      console.log('  -> FAIL: Threw on degraded 503:', err);
      failed++;
    }
  });

  // Summary
  console.log('\n========================================================');
  console.log(` RESULTS: ${passed} PASSED, ${failed} FAILED`);
  console.log('========================================================');
  if (failed > 0) {
    process.exitCode = 1;
  }
}

runTests();
