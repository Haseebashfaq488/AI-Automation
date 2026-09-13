// Probe: open WhatsApp Web with the real Chrome profile, check login,
// scrape the top of the chat list. Sends nothing.
const puppeteer = require("puppeteer");

(async () => {
  const browser = await puppeteer.launch({
    headless: "new",
    timeout: 120000,
    channel: "chrome",
    userDataDir: process.env.CHROME_USER_DATA,
    args: [
      "--no-sandbox",
      "--disable-gpu",
      `--profile-directory=${process.env.CHROME_PROFILE}`,
      "--window-size=1280,900",
      "--no-first-run",
      "--no-default-browser-check",
    ],
    defaultViewport: { width: 1280, height: 900 },
  });
  const page = await browser.newPage();
  await page.goto("https://web.whatsapp.com", { waitUntil: "domcontentloaded", timeout: 90000 });
  await new Promise((r) => setTimeout(r, 10000));

  const info = await page.evaluate(() => {
    const pane = document.querySelector("#pane-side");
    const items = [...document.querySelectorAll('#pane-side [role="listitem"], #pane-side [data-testid="cell-frame-container"]')].slice(0, 8);
    return {
      loggedIn: !!pane && pane.innerText.trim().length > 0,
      bodyTextStart: document.body.innerText.slice(0, 120),
      sample: items.map((i) => i.innerText.split("\n").slice(0, 2).join(" | ")),
    };
  });
  console.log("LOGGED IN:", info.loggedIn);
  console.log("PAGE TEXT:", JSON.stringify(info.bodyTextStart));
  console.log("TOP CHATS:", JSON.stringify(info.sample, null, 1));
  await browser.close();
})().catch((e) => { console.error("FATAL:", e.message); process.exit(1); });
