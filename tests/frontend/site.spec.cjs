const { test, expect } = require('@playwright/test');
const path = require('node:path');
const { createHash } = require('node:crypto');
const mathRoot = path.dirname(require.resolve('mathjax/package.json'));

async function localNetwork(page, prefix, { math = true } = {}) {
  await page.context().route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.origin === 'http://127.0.0.1:8765') return route.continue();
    const marker = '/npm/mathjax@3.2.2/';
    if (math && url.origin === 'https://cdn.jsdelivr.net' && url.pathname.startsWith(marker)) {
      const filename = path.resolve(mathRoot, url.pathname.slice(marker.length));
      if (!filename.startsWith(mathRoot + path.sep)) return route.abort();
      return route.fulfill({ path: filename });
    }
    // MkDocs intentionally gives the special 404 page absolute canonical assets.
    if (url.origin === 'https://pyeuvics.github.io') {
      const response = await page.request.get(`http://127.0.0.1:8765${prefix}${url.pathname}`);
      return route.fulfill({ response });
    }
    return route.abort();
  });
}

for (const prefix of ['/scaffold', '/assembled/site']) {
  test.describe(prefix, () => {
    test.beforeEach(async ({ page }) => localNetwork(page, prefix));

    test('desktop navigation, headings, captions and real equations', async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 1000 });
      const errors=[];page.on('pageerror', error => errors.push(error.message));
      await page.goto(`${prefix}/project/overview/`);
      await expect(page.locator('h1')).toHaveCount(1);
      await expect(page.locator('.md-sidebar--primary')).toBeVisible();
      await expect(page.locator('.arithmatex mjx-container').first()).toBeVisible();
      expect(await page.locator('mjx-merror').count()).toBe(0);
      await page.evaluate(()=>MathJax.startup.promise);
      const count=await page.locator('mjx-container').count();
      await page.evaluate(async () => {EuvicsMath.initialize();EuvicsMath.initialize();await EuvicsMath.render();});
      expect(await page.locator('mjx-container').count()).toBe(count);
      const image=page.locator('.ics-schematic img');
      await expect(image).toHaveAttribute('alt', /electron bunch/);
      const description=await image.getAttribute('aria-describedby');
      await expect(page.locator(`#${description}`)).toBeVisible();
      expect(await image.evaluate(el => el.naturalWidth > 0)).toBe(true);
      const headings=await page.locator('article h1, article h2, article h3').evaluateAll(els=>els.map(el=>Number(el.tagName.slice(1))));
      expect(headings[0]).toBe(1);
      for(let i=1;i<headings.length;i++) expect(headings[i]-headings[i-1]).toBeLessThanOrEqual(1);
      expect(errors).toEqual([]);
    });

    test('mobile keyboard drawer is idempotent and restores focus', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto(`${prefix}/`);
      await page.evaluate(()=>{for(let i=0;i<5;i++) EuvicsNavigation.initialize();});
      const menu=page.getByRole('button',{name:/^(Open|Close) navigation$/});
      await menu.focus();await page.keyboard.press('Enter');
      await expect(page.locator('#__drawer')).toBeChecked();
      await expect(menu).toHaveAttribute('aria-expanded','true');
      await page.keyboard.press('Escape');
      await expect(menu).toBeFocused();
      await expect(page.locator('#__drawer')).not.toBeChecked();
      await page.keyboard.press('Space');
      await expect(page.locator('#__drawer')).toBeChecked();
      const overview=page.locator('.md-nav--primary a').filter({hasText:'Overview'}).first();
      await overview.focus();await page.keyboard.press('Enter');
      await expect(page).toHaveURL(new RegExp(`${prefix}/project/overview/$`));
      await expect(page.locator('h1')).toContainText(/overview/i);
    });

    test('search returns a keyboard reachable local result', async ({ page }) => {
      await page.setViewportSize({width:1440,height:1000});
      await page.goto(`${prefix}/`);
      const search=page.getByRole('textbox',{name:'Search',exact:true});
      await search.pressSequentially('conventions',{delay:30});
      const result=page.locator('.md-search-result__link').first();
      await expect(result).toBeVisible();
      expect(new URL(await result.getAttribute('href'),page.url()).origin).toBe('http://127.0.0.1:8765');
      await search.press('ArrowDown');
      await expect(result).toBeFocused();
      await page.keyboard.press('Enter');
      await expect(page.locator('h1')).toBeVisible();
      expect(page.url()).toContain(`${prefix}/`);
    });

    test('narrow layout, zoom, focus contrast and reduced motion', async ({ page }) => {
      await page.setViewportSize({width:390,height:844});
      await page.emulateMedia({reducedMotion:'reduce'});
      await page.goto(`${prefix}/project/overview/`);
      const dimensions=await page.locator('.ics-schematic > p').evaluate(el=>({width:el.clientWidth,scroll:el.scrollWidth,overflow:getComputedStyle(el).overflowX}));
      expect(dimensions.scroll).toBeGreaterThan(dimensions.width);
      expect(dimensions.overflow).toBe('auto');
      expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(391);
      // Stress actual component CSS with wide content, independent of scientific prose.
      await page.locator('article').evaluate(el=>el.insertAdjacentHTML('beforeend','<table id="wide"><tr><td>'+ 'longword'.repeat(80)+'</td></tr></table>'));
      expect(await page.locator('#wide').evaluate(el=>el.scrollWidth>el.clientWidth && getComputedStyle(el).overflowX==='auto')).toBe(true);
      await page.setViewportSize({width:640,height:900});
      await page.locator('body').evaluate(el=>el.style.zoom='2');
      expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(641);
      const link=page.locator('article a').first();await link.focus();
      const focus=await link.evaluate(el=>({outline:getComputedStyle(el).outlineColor,shadow:getComputedStyle(el).boxShadow,width:getComputedStyle(el).outlineWidth}));
      expect(focus.width).toBe('3px');expect(focus.outline).toMatch(/^rgb/);expect(focus.shadow).toContain('rgb(23, 33, 43)');
      const contrast=(a,b)=>{const luminance=c=>c.map(x=>x/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4).reduce((s,x,i)=>s+x*[.2126,.7152,.0722][i],0);const x=luminance(a),y=luminance(b);return(Math.max(x,y)+.05)/(Math.min(x,y)+.05);};
      expect(contrast(focus.outline.match(/\d+/g).map(Number),[23,33,43])).toBeGreaterThan(3);
      expect(contrast([36,114,164],[255,255,255])).toBeGreaterThan(4.5);
      expect(await link.evaluate(el=>parseFloat(getComputedStyle(el).transitionDuration))).toBeLessThanOrEqual(.00001);
    });

    test('print retains content and bounded figures, hides navigation', async ({ page }) => {
      await page.goto(`${prefix}/project/overview/`);await page.emulateMedia({media:'print'});
      await expect(page.locator('.md-header')).toBeHidden();await expect(page.locator('.md-sidebar--primary')).toBeHidden();
      await expect(page.locator('h1')).toBeVisible();await expect(page.locator('.ics-schematic figcaption')).toBeVisible();
      expect(await page.locator('.ics-schematic img').evaluate(el=>el.getBoundingClientRect().width<=el.closest('article').getBoundingClientRect().width)).toBe(true);
    });

    test('missing paths return the local custom 404 with a route home', async ({ page }) => {
      const response=await page.goto(`${prefix}/missing-page/`);expect(response.status()).toBe(404);
      await expect(page.locator('h1')).toContainText('Page not found');
      await expect(page.getByRole('link',{name:/home/i}).first()).toBeVisible();
    });
  });
}

test('assembled downloads and notebook retain accessible provenance',async({page})=>{
  await localNetwork(page,'/assembled/site');await page.goto('/assembled/site/downloads/');
  const link=page.locator('article a[href$=".pdf"]').first();await expect(link).toBeVisible();
  const url=await link.evaluate(el=>el.href);const response=await page.request.get(url);expect(response.status()).toBe(200);
  const bytes=await response.body();expect(bytes.subarray(0,5).toString()).toBe('%PDF-');
  await expect(page.locator('article')).toContainText(createHash('sha256').update(bytes).digest('hex'));
  await expect(page.locator('article')).toContainText('Known limitations');
  await page.goto('/assembled/site/software/notebooks/');
  // The rendered notebook link is selected by its documented title rather than a source download.
  const rendered=page.locator('article a[href*="00_environment_check"]').first();
  await expect(rendered).toBeVisible();await rendered.click();
  await expect(page.locator('article')).toContainText('Browser fixture notebook');
  await expect(page.locator('h1')).toHaveCount(1);
});

test('MathJax delivery failure is visible and does not break navigation',async({page})=>{
  await localNetwork(page,'/scaffold',{math:false});await page.goto('/scaffold/project/overview/');
  await expect(page.getByRole('status').filter({hasText:'Equation rendering is unavailable'})).toBeVisible();
  await expect(page.locator('.arithmatex').first()).toContainText('\\');
});
