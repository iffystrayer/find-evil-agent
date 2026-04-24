import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Find Evil Agent demo recording
 *
 * Features:
 * - Automatic video recording at 1080p
 * - Screenshot capture on failure
 * - Trace collection for debugging
 * - Slow-mo for demo clarity
 */
export default defineConfig({
  testDir: './tests',

  // Timeout settings for demo actions
  timeout: 5 * 60 * 1000, // 5 minutes per test (for slow LLM responses)
  expect: {
    timeout: 60 * 1000, // 60 seconds for assertions
  },

  // Run tests in sequence for demo recording
  fullyParallel: false,

  // Retry settings
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,

  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list'],
    ['json', { outputFile: 'test-results.json' }],
  ],

  // Global settings
  use: {
    // Base URL for React UI
    baseURL: 'http://localhost:15173',

    // Browser settings
    headless: false, // Always show browser for demo
    viewport: { width: 1920, height: 1080 },

    // Slow motion for demo clarity (milliseconds between actions)
    launchOptions: {
      slowMo: 1000, // 1 second delay between actions
    },

    // Screenshot settings
    screenshot: 'only-on-failure',

    // Video recording (always record for demo)
    video: {
      mode: 'on',
      size: { width: 1920, height: 1080 },
    },

    // Trace collection (for debugging)
    trace: 'on-first-retry',
  },

  // Project configurations
  projects: [
    {
      name: 'demo-recording',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
        launchOptions: {
          slowMo: 800, // Slower for demo recording
          args: [
            '--start-maximized',
            '--disable-blink-features=AutomationControlled',
          ],
        },
        video: {
          mode: 'on',
          size: { width: 1920, height: 1080 },
        },
      },
    },

    {
      name: 'fast-testing',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          slowMo: 0, // No delay for fast testing
        },
        video: 'off',
      },
    },
  ],

  // Output directory
  outputDir: 'test-results/',

  // Web server configuration (optional - services should already be running)
  // webServer: {
  //   command: 'npm run dev',
  //   url: 'http://localhost:15173',
  //   reuseExistingServer: true,
  //   timeout: 120 * 1000,
  // },
});
