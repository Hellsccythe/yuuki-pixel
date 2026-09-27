// PLAYWRIGHT_PATH points at an installed Playwright; serve repository on port 8765.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('response', r => { if (r.status() >= 400) errors.push(r.url()+': '+r.status()); });
  const output = path.resolve(__dirname, '../Logs/gallery');
  fs.mkdirSync(output, { recursive: true });
  try {
    await page.goto('http://127.0.0.1:8765/preview/assets.html');
    await page.waitForSelector('.card');
    assert.equal(await page.locator('.card').count(), 61);
    // Check the entire catalog, including lazy-loaded off-screen pictures.
    const sizes = await page.evaluate(async () => {
      const data = await (await fetch('../Assets/Game/Resources/Environment/catalog.json')).json();
      return Promise.all(data.assets.map(a => new Promise(resolve => {
        const im = new Image();
        im.onload = () => resolve(im.naturalWidth===a.width && im.naturalHeight===a.height);
        im.onerror = () => resolve(false); im.src = '../'+a.path;
      })));
    });
    assert(sizes.every(Boolean), 'All 61 PNGs must load at their recorded size');
    await page.locator('#category').selectOption({label:'Dungeon'});
    assert.equal(await page.locator('.card').count(), 9);
    await page.locator('.card').filter({hasText:'Altar quebrado'}).click();
    assert(await page.locator('#detail').evaluate(d=>d.open));
    await page.locator('#large').evaluate(im=>im.decode());
    await page.screenshot({path:path.join(output,'altar.png')});
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#detail').evaluate(d=>d.open), false);
    await page.locator('#category').selectOption({label:'Todos'});
    await page.locator('#search').fill('pao');
    assert.equal(await page.locator('.card').count(), 1, 'accent-insensitive search');
    await page.locator('#search').fill('');
    await page.locator('.art img').evaluateAll(images => Promise.all(images.map(im => { im.loading='eager'; return im.decode(); })));
    assert(await page.locator('.art img').evaluateAll(images => images.every(im => {
      const parent=im.parentElement.getBoundingClientRect(), rect=im.getBoundingClientRect();
      return rect.width<=parent.width && rect.height<=parent.height;
    })), 'thumbnails stay inside their cards');
    await page.screenshot({path:path.join(output,'catalog-desktop.png')});
    await page.setViewportSize({width:390,height:844});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth), 'no mobile overflow');
    await page.locator('.card').first().click();
    await page.locator('#large').evaluate(im=>im.decode());
    assert(await page.locator('#close').isVisible());
    await page.screenshot({path:path.join(output,'catalog-mobile.png')});
    assert.deepEqual(errors, []);
    console.log('PASS: 61 images, categories, accent search, enlargement, Escape, mobile layout; no browser errors.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });
