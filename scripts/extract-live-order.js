const { chromium } = require('playwright');
(async()=>{
  const browser = await chromium.launch({headless:true});
  const page = await browser.newPage({ viewport: { width: 1365, height: 900 } });
  await page.goto('https://www.compassstarcelebrations.com/gallery', { waitUntil: 'networkidle' });
  for (let i=0;i<18;i++) {
    await page.evaluate(() => window.scrollBy(0, window.innerHeight * 0.95));
    await page.waitForTimeout(450);
  }
  await page.waitForTimeout(1200);
  const urls = await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('main img'))
      .map(i => i.currentSrc || i.src)
      .filter(Boolean)
      .filter(u => /wixstatic\.com\/media\//.test(u));
    return all;
  });
  const cleaned = urls.map(u => {
    const m = u.match(/\/media\/([^/?]+(?:~mv2\.(?:jpg|jpeg|png))?)/i);
    return m ? m[1] : u;
  });
  const uniq = [];
  for (const c of cleaned) if (!uniq.includes(c)) uniq.push(c);
  console.log('count=' + uniq.length);
  console.log(JSON.stringify(uniq, null, 2));
  await browser.close();
})();
