const { chromium } = require('playwright-core');
const EXE = 'C:\\Users\\Administrator\\AppData\\Local\\ms-playwright\\chromium-1247\\chrome-win64\\chrome.exe';

(async () => {
  const browser = await chromium.launch({ executablePath: EXE, headless: true });
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  await page.goto('http://127.0.0.1:8721/', { waitUntil: 'networkidle' });

  // 1. 首页空态
  await page.screenshot({ path: 'docs/screenshot-home.png' });

  // 2. PDF 原件 + 句级高亮
  await page.setInputFiles('#fileInput', 'tests/test.pdf');
  await page.waitForTimeout(2500);
  await page.click('.viewtab[data-view="pdf"]');
  await page.waitForTimeout(3500);
  await page.evaluate(() => {
    locateInPdf('The Supreme Court has long recognized that a corporation may be treated as a person');
  });
  await page.waitForTimeout(800);
  await page.screenshot({ path: 'docs/screenshot-pdf.png' });

  // 3. 双语对照（重新加载 + 注入 demo）
  await page.goto('http://127.0.0.1:8721/', { waitUntil: 'networkidle' });
  await page.click('#btnSample');
  await page.waitForTimeout(400);
  await page.evaluate(() => {
    state.docType = 'text';
    state.segments = [{
      raw: 'demo', sentences: [
        { original: 'The Foreign Corrupt Practices Act of 1977, as amended, 15 U.S.C. 78dd-1 et seq., was enacted for the purpose of making it unlawful for certain classes of persons and entities to make payments to foreign government officials to assist in obtaining or retaining business.',
          translation: '1977 年《反海外腐败法》（经修订，载于 15 U.S.C. § 78dd-1 及以下条文）的立法目的，在于禁止特定类别的主体与实体向外国政府官员支付款项，以协助获取或保留业务。',
          terms: [{ term: 'Foreign Corrupt Practices Act', explain: '《反海外腐败法》，美国规制海外商业贿赂的核心法律' }],
          point: 'FCPA 的立法目的是禁止为获取或保留业务而向外国官员行贿', pointConfidence: 'high',
          references: [{ title: '15 U.S.C. § 78dd-1', note: '作为被解释的法条依据', type: 'statute', confidence: 'high' }] },
        { original: 'The Supreme Court has long recognized that a corporation may be treated as a person. See Citizens United v. Federal Election Commission, 558 U.S. 310 (2010).',
          translation: '最高法院长期以来承认，公司可被视为法律上的「人」。参见 Citizens United v. Federal Election Commission, 558 U.S. 310 (2010)。',
          terms: [{ term: 'corporation', explain: '法人，法律上拟制的独立主体' }],
          point: '公司可作为法律上的「人」对待', pointConfidence: 'high',
          references: [{ title: 'Citizens United v. FEC, 558 U.S. 310 (2010)', note: '作为权威判例依据', type: 'case', confidence: 'high' }] },
        { original: 'Under the General Data Protection Regulation (Regulation (EU) 2016/679), the processing of personal data is lawful only if at least one of the legal bases in Article 6 applies.',
          translation: '根据《通用数据保护条例》（Regulation (EU) 2016/679），个人数据的处理仅当满足第 6 条所列至少一项合法事由时才属合法。',
          terms: [{ term: 'processing', explain: '处理，对个人数据进行的任何操作' }],
          point: 'GDPR 要求数据处理须有第 6 条合法事由', pointConfidence: 'high',
          references: [{ title: 'Regulation (EU) 2016/679', note: '作为被解释的法规依据', type: 'eu_reg', confidence: 'high' }] },
      ]
    }];
    render();
  });
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'docs/screenshot-bilingual.png' });

  // 4. 底部 sheet 拉高展示术语表
  await page.evaluate(() => { document.querySelector('#summary').style.height = '60vh'; });
  await page.waitForTimeout(400);
  await page.screenshot({ path: 'docs/screenshot-summary.png' });

  await browser.close();
  console.log('截图完成');
})();
