// Run with Playwright available in NODE_PATH and the site served on port 8765.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({channel: 'chrome', headless: true});
  try {
    const page = await browser.newPage({viewport: {width:1440,height:1000}});
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto('http://127.0.0.1:8765/visualisasi.html');
    await page.waitForSelector('.paper-card');
    assert.equal(await page.locator('.paper-card').count(),24);
    assert.equal(await page.locator('.paper-preview').count(),13);
    await page.locator('#paper-search').fill('NumPy');
    assert.equal(await page.locator('.paper-card:visible').count(),1);
    assert.match(await page.locator('.paper-card:visible').innerText(),/Array programming/);
    await page.locator('#reset-filters').click();
    await page.locator('#journal-filter').selectOption('PLOS Biology');
    assert.equal(await page.locator('.paper-card:visible').count(),1);
    await page.locator('#reset-filters').click();
    await page.locator('#topic-filter').selectOption('Bacaan pendamping');
    assert.equal(await page.locator('.paper-card:visible').count(),1);
    await page.locator('#reset-filters').click();
    await page.locator('#access-filter').selectOption('local');
    assert.equal(await page.locator('.paper-card:visible').count(),13);
    await page.locator('#access-filter').selectOption('external');
    assert.equal(await page.locator('.paper-card:visible').count(),11);
    await page.locator('#paper-search').fill('tidak-ada-paper-ini');
    assert.equal(await page.locator('.paper-card:visible').count(),0);
    assert.equal(await page.locator('#empty-state').isVisible(),true);
    await page.locator('#reset-filters').click();
    await page.locator('#paper-14 .paper-preview').click();
    assert.equal(await page.locator('#preview-dialog').isVisible(),true);
    assert.match(await page.locator('#preview-pdf').getAttribute('href'),/#page=2$/);
    await page.keyboard.press('Escape');
    assert.equal(await page.locator('#preview-dialog').isVisible(),false);
    await page.goto('http://127.0.0.1:8765/visualisasi.html#paper-08');
    await page.waitForSelector('#paper-08');
    await page.waitForTimeout(500);
    assert.equal(await page.locator('#paper-08').isVisible(),true);
    await page.goto('http://127.0.0.1:8765/visualisasi.html');
    await page.waitForSelector('.paper-card');
    await page.screenshot({path:'/private/tmp/gallery-desktop.png',fullPage:false});
    // Load every lazy preview before testing image decoding.
    await page.locator('img').evaluateAll(imgs => imgs.forEach(img => img.loading='eager'));
    await page.waitForFunction(() => [...document.querySelectorAll('.paper-preview img')].every(img => img.complete && img.naturalWidth > 0));
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),false);
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:'/private/tmp/gallery-mobile.png',fullPage:false});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),false);
    await page.locator('#paper-search').fill('NumPy');
    await page.locator('#paper-04').scrollIntoViewIfNeeded();
    await page.screenshot({path:'/private/tmp/gallery-mobile-card.png',fullPage:false});
    await page.goto('http://127.0.0.1:8765/');
    await page.waitForSelector('[data-prompt-role="editor"]');
    assert.equal(await page.locator('a[href="visualisasi.html"]').count(),2);
    await page.locator('.tab[data-tab="reviewer"]').click();
    assert.equal(await page.locator('#reviewer').evaluate(e => e.classList.contains('active-panel')),true);
    assert.deepEqual(errors,[]);
    console.log('PASS: 24 cards, 13 images, search, combined filters, reset, empty state, modal/Escape, deep link, desktop/mobile overflow, decoded images, home links and existing reviewer tab.');
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error);process.exit(1);});
