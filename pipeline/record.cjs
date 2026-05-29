// 用 Playwright 錄製 index.html（?render=true 自動播放、無聲 webm）
// 總片長 181 秒，錄 181.8 秒留緩衝
const { chromium } = require('playwright');
const path = require('path');
const PROJECT_DIR = __dirname;

(async () => {
  console.log('Starting Playwright Chromium...');
  const browser = await chromium.launch({
    args: ['--autoplay-policy=no-user-gesture-required', '--mute-audio', '--no-sandbox', '--disable-setuid-sandbox'],
  });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: 1,
    recordVideo: { dir: path.join(PROJECT_DIR, 'renders'), size: { width: 1920, height: 1080 } },
  });
  const page = await context.newPage();
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.error('PAGE ERROR:', err.stack || err.message));

  const fileUrl = 'file:///' + path.join(PROJECT_DIR, 'index.html').replace(/\\/g, '/') + '?render=true';
  console.log('Loading (Render Mode):', fileUrl);
  await page.goto(fileUrl);

  console.log('Recording 181.8 seconds...');
  await page.waitForTimeout(181800);

  console.log('Closing browser...');
  await context.close();
  await browser.close();
  console.log('Recording completed.');
})();
