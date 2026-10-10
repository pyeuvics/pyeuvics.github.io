const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: './tests/frontend',
  testMatch: '*.spec.cjs',
  workers: 1,
  retries: 0,
  forbidOnly: true,
  timeout: 30000,
  globalTimeout: 300000,
  outputDir: '.staging/browser-results',
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:8765', browserName: 'chromium', serviceWorkers: 'block', trace: 'retain-on-failure' },
  webServer: {
    command: 'python -m tests.support.frontend --port 8765',
    url: 'http://127.0.0.1:8765/scaffold/',
    timeout: 120000,
    reuseExistingServer: false,
    env: { PYTHONDONTWRITEBYTECODE: '1' }
  }
});
