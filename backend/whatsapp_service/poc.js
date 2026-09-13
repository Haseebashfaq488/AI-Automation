/**
 * DOM proof-of-concept: can WE drive WhatsApp Web directly?
 *
 * Usage:  node poc.js <phone-with-country-code> [message]
 * Example: node poc.js 491701234567 "Hello from Jarvis"
 *
 * Flow:
 *  1. Launch Chrome with a persistent profile (./dom_profile)
 *  2. If not logged in: screenshot the page's QR -> qr_dom.png, wait for scan
 *  3. Navigate to web.whatsapp.com/send?phone=..&text=.. and click Send
 *  4. Verify the outgoing bubble appears in the DOM
 */
const puppeteer = require("puppeteer");
const path = require("path");

const PHONE = (process.argv[2] || "").replace(/\D/g, "");
const TEXT = process.argv[3] || "Hello from Jarvis (DOM test)";

if (!PHONE) {
  console.error("Usage: node poc.js <phone-with-country-code> [message]");
  process.exit(1);
}

// Use the real Chrome profile when CHROME_USER_DATA + CHROME_PROFILE are set
// (e.g. the profile where WhatsApp Web is already logged in). Otherwise fall
// back to our own throwaway profile in ./dom_profile.
const USE_REAL_PROFILE = !!process.env.CHROME_USER_DATA;
const PROFILE_DIR = process.env.CHROME_USER_DATA || path.join(__dirname, "dom_profile");
const PROFILE_NAME = process.env.CHROME_PROFILE || "";
const QR_SHOT = path.join(__dirname, "qr_dom.png");

async function launchBrowser() {
  const options = {
    headless: true,
    args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--window-size=1280,900"],
    defaultViewport: { width: 1280, height: 900 },
  };
  if (USE_REAL_PROFILE) {
    options.channel = "chrome"; // launch the installed Google Chrome
    options.userDataDir = PROFILE_DIR;
    if (PROFILE_NAME) options.args.push(`--profile-directory=${PROFILE_NAME}`);
  } else {
    options.userDataDir = PROFILE_DIR;
  }
  return puppeteer.launch(options);
}

async function isLoggedIn(page) {
  return page.evaluate(() => {
    const pane = document.querySelector("#pane-side");
    return !!pane && pane.innerText.trim().length > 0;
  });
}

async function waitForLogin(page) {
  console.log("[poc] checking login state...");
  for (let attempt = 0; attempt < 60; attempt++) {
    if (await isLoggedIn(page)) {
      console.log("[poc] logged in!");
      return true;
    }
    // refresh the QR screenshot every ~15s so it stays scannable
    if (attempt % 3 === 0) {
      await page.screenshot({ path: QR_SHOT });
      console.log(`[poc] QR screenshot saved -> qr_dom.png (waiting... ${attempt * 5}s)`);
    }
    await new Promise((r) => setTimeout(r, 5000));
  }
  return false;
}

async function clickSend(page) {
  const candidates = [
    'button span[data-icon="send"]',
    '[data-testid="send"]',
    'footer span[data-icon="send"]',
    'span[data-icon="send"]',
    'button[aria-label*="Send" i]',
    'button[aria-label*="send" i]',
  ];
  for (const sel of candidates) {
    try {
      const el = await page.waitForSelector(sel, { timeout: 5000 });
      if (el) {
        await el.click();
        return sel;
      }
    } catch (_) { /* try next selector */ }
  }
  return null;
}

async function main() {
  console.log(USE_REAL_PROFILE
    ? `[poc] launching installed Chrome with profile "${PROFILE_NAME || "Default"}")...`
    : "[poc] launching Chrome with own profile...");
  const browser = await launchBrowser();
  const page = await browser.newPage();
  page.setDefaultTimeout(60000);

  console.log("[poc] opening WhatsApp Web...");
  await page.goto("https://web.whatsapp.com", { waitUntil: "domcontentloaded", timeout: 90000 });
  // let the app boot
  await new Promise((r) => setTimeout(r, 8000));

  if (!(await waitForLogin(page))) {
    console.error("[poc] timed out waiting for QR scan");
    await browser.close();
    process.exit(2);
  }

  // --- send via the stable /send URL scheme ---------------------------------
  const url = `https://web.whatsapp.com/send?phone=${PHONE}&text=${encodeURIComponent(TEXT)}`;
  console.log(`[poc] navigating to send URL for +${PHONE} ...`);
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 90000 });
  await new Promise((r) => setTimeout(r, 6000));

  const used = await clickSend(page);
  if (!used) {
    console.error("[poc] could not find the send button — selectors may have changed");
    await page.screenshot({ path: path.join(__dirname, "poc_fail.png") });
    await browser.close();
    process.exit(3);
  }
  console.log(`[poc] clicked send via selector: ${used}`);

  // --- verify an outgoing bubble appeared ------------------------------------
  await new Promise((r) => setTimeout(r, 4000));
  const sent = await page.evaluate(() => {
    const mine = document.querySelectorAll('[data-testid="msg-container"] .message-out, .message-out');
    return mine.length;
  });
  console.log(`[poc] outgoing messages visible in DOM: ${sent}`);
  await page.screenshot({ path: path.join(__dirname, "poc_result.png") });
  console.log(sent > 0 ? "[poc] SUCCESS ✅" : "[poc] clicked but no outgoing bubble found ⚠️");

  await browser.close();
  process.exit(sent > 0 ? 0 : 4);
}

main().catch((err) => {
  console.error("[poc] fatal:", err.message);
  process.exit(1);
});
