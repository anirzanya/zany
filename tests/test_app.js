const { chromium } = require('playwright-core');

const EXE = 'C:\\Users\\Administrator\\AppData\\Local\\ms-playwright\\chromium-1247\\chrome-win64\\chrome.exe';
const BASE = 'http://127.0.0.1:8721/';

(async () => {
  const results = [];
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const page = await browser.newPage();
  const jsErrors = [];
  page.on('pageerror', e => jsErrors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') jsErrors.push('console: ' + m.text()); });

  const check = (name, cond, extra='') => {
    results.push({ name, pass: !!cond, extra });
    console.log((cond ? '✅' : '❌') + ' ' + name + (extra ? ' — ' + extra : ''));
  };

  // 1. 页面加载
  await page.goto(BASE, { waitUntil: 'domcontentloaded' });
  const title = await page.title();
  check('页面标题', title.includes('LegalReader'), title);

  // 2. 空态 dropzone
  const dropzone = await page.isVisible('#dropzone');
  check('空态 dropzone 显示', dropzone);

  // 3. 示例按钮载入文本
  await page.click('#btnSample');
  await page.waitForTimeout(300);
  const workspaceVisible = await page.isVisible('#workspace');
  check('示例载入后工作区显示', workspaceVisible);
  const runEnabled = await page.isEnabled('#btnRun');
  check('「开始解读」按钮激活', runEnabled);

  // 4. 引注高亮（示例文本含 558 U.S. 310 等引注）
  const citeCount = await page.evaluate(() => document.querySelectorAll('#leftBody .cite').length);
  check('原文引注高亮存在', citeCount > 0, citeCount + ' 个引注');

  // 5. 无 key 时点开始解读 → 提示 + 自动打开设置（先清空 key）
  await page.evaluate(() => fetch('/api/config', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({api_key:''})}));
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.click('#btnSample');
  await page.waitForTimeout(300);
  await page.click('#btnRun');
  await page.waitForTimeout(1500);
  const toastText = await page.evaluate(() => document.querySelector('#toast')?.textContent || '');
  check('无 key 提示', toastText.includes('Key') || toastText.includes('key') || toastText.includes('设置'), toastText);

  // 6. 无 key 时自动打开设置面板
  await page.waitForTimeout(300);
  const settingsAutoOpen = await page.isVisible('#settings');
  check('无 key 自动打开设置', settingsAutoOpen);
  if (settingsAutoOpen) { await page.click('#btnCloseSet'); await page.waitForTimeout(200); }

  // 7. 设置面板手动打开
  await page.click('#btnSettings');
  await page.waitForTimeout(200);
  const settingsVisible = await page.isVisible('#settings');
  check('设置面板手动打开', settingsVisible);
  await page.click('#btnCloseSet');
  await page.waitForTimeout(200);

  // 8. 底部 summary 4 个 tab
  await page.click('#btnSample');
  await page.waitForTimeout(300);
  const tabs = await page.evaluate(() => Array.from(document.querySelectorAll('.sum-tab')).map(t => t.textContent.trim()));
  check('底部 tab 齐全', tabs.length === 4 && tabs.includes('测验'), tabs.join('/'));

  // 9. 测验 tab 点击（无解读内容，应显示生成按钮）
  await page.click('.sum-tab[data-tab="quiz"]');
  await page.waitForTimeout(200);
  const quizContent = await page.evaluate(() => document.querySelector('#sumContent')?.textContent || '');
  check('测验 tab 响应', quizContent.includes('生成测验'), quizContent.slice(0, 30));

  // 10. 设置面板字段（含阅读深度）
  await page.click('#btnSettings');
  await page.waitForTimeout(200);
  const hasKeyField = await page.isVisible('#setKey');
  const hasModel = await page.isVisible('#setModel');
  const hasDepth = await page.isVisible('#setDepth');
  const hasClToken = await page.isVisible('#setClToken');
  const depthOptions = await page.evaluate(() => Array.from(document.querySelectorAll('#setDepth option')).map(o => o.value));
  check('设置字段完整(含深度/CourtListener)', hasKeyField && hasModel && hasDepth && hasClToken);
  check('阅读深度三档', depthOptions.includes('quick') && depthOptions.includes('standard') && depthOptions.includes('deep'), depthOptions.join('/'));
  await page.click('#btnCloseSet');

  // 11. 连接状态指示器
  const connText = await page.evaluate(() => document.querySelector('#connText')?.textContent || '');
  check('连接状态指示器', connText.includes('未配置'), connText);

  console.log('\n=== JS 错误 ===');
  jsErrors.forEach(e => console.log('  ' + e));
  check('无 JS 错误（忽略 favicon 与预期 400）', jsErrors.filter(e => !e.includes('favicon') && !e.includes('400')).length === 0, jsErrors.filter(e=>!e.includes('favicon')&&!e.includes('400')).length + ' 个非预期错误');

  const passed = results.filter(r => r.pass).length;
  console.log('\n=== 结果: ' + passed + '/' + results.length + ' 通过 ===');

  await browser.close();
})();
