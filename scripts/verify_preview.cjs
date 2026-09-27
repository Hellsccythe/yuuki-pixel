// Run with Node and PLAYWRIGHT_PATH pointing to an installed Playwright package.
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const { chromium } = require(process.env.PLAYWRIGHT_PATH || 'playwright');

(async () => {
  const browser = await chromium.launch({
    channel: 'msedge', headless: true,
  });
  const page = await browser.newPage({ viewport: { width: 1100, height: 850 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', response => {
    if (response.status() >= 400) errors.push(response.status() + ': ' + response.url());
  });
  const output = path.resolve(__dirname, '../Temp/preview-qa-v3');
  fs.mkdirSync(output, { recursive: true });
  try {
    await page.addInitScript(() => {
      window.spriteDraws = [];
      const original = CanvasRenderingContext2D.prototype.drawImage;
      CanvasRenderingContext2D.prototype.drawImage = function (image, ...args) {
        if (image.src && image.src.includes('Yuuki_')) {
          window.spriteDraws.push({ image: image.src, column: args[0] / 512, row: args[1] / 512, smooth: this.imageSmoothingEnabled });
        }
        return original.call(this, image, ...args);
      };
    });
    await page.goto('http://127.0.0.1:8765/preview/game.html?v=3');
    await page.waitForFunction(() => window.spriteDraws.length > 2);
    assert.match(await page.locator('#state').textContent(), /idle · right/);
    let draw = await page.evaluate(() => window.spriteDraws.at(-1));
    assert.match(draw.image, /Yuuki_Idle_2x1/);
    assert.equal(draw.column, 1);
    await page.screenshot({ path: path.join(output, 'idle-right.png') });

    for (const [direction, key, row] of [['right', 'ArrowRight', 1], ['left', 'ArrowLeft', 0]]) {
      await page.keyboard.down(key);
      await page.waitForTimeout(800);
      assert.match(await page.locator('#state').textContent(), new RegExp('walk · ' + direction));
      draw = await page.evaluate(() => window.spriteDraws.at(-1));
      assert.equal(draw.row, row);
      await page.screenshot({ path: path.join(output, 'walk-' + direction + '.png') });
      await page.keyboard.down('Shift');
      await page.waitForTimeout(550);
      assert.match(await page.locator('#state').textContent(), new RegExp('run · ' + direction));
      draw = await page.evaluate(() => window.spriteDraws.at(-1));
      assert.equal(draw.row, row + 2);
      await page.screenshot({ path: path.join(output, 'run-' + direction + '.png') });
      await page.keyboard.up('Shift');
      await page.keyboard.up(key);
      await page.waitForTimeout(100);
      assert.match(await page.locator('#state').textContent(), new RegExp('idle · ' + direction));
      await page.screenshot({ path: path.join(output, 'idle-' + direction + '.png') });

      await page.evaluate(() => { window.spriteDraws = []; });
      await page.keyboard.press('Space');
      await page.waitForTimeout(230);
      assert.match(await page.locator('#state').textContent(), new RegExp('jump · ' + direction));
      await page.screenshot({ path: path.join(output, 'jump-' + direction + '.png') });
      await page.waitForTimeout(800);
      const columns = await page.evaluate(jumpRow => [...new Set(window.spriteDraws.filter(d => d.row === jumpRow && d.image.includes('Movement')).map(d => d.column))].sort(), row + 4);
      assert.deepEqual(columns, [0, 1, 2, 3, 4, 5], 'Jump must display every frame: ' + direction);
      assert.match(await page.locator('#state').textContent(), new RegExp('idle · ' + direction));
    }
    assert.equal(await page.evaluate(() => window.spriteDraws.some(d => d.smooth)), false);
    assert.deepEqual(errors, []);
    await page.goto('http://127.0.0.1:8765/preview/directions.html?v=3');
    await page.locator('#clip').selectOption('6');
    assert.match(await page.locator('#status').textContent(), /pose neutra estática/);
    await page.locator('#clip').selectOption('7');
    assert.match(await page.locator('#status').textContent(), /direita/);
    console.log(JSON.stringify({ passed: true, states: 'idle/walk/run/jump left and right', allJumpFrames: true, errors, screenshots: output }));
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
