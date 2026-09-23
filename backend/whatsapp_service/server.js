/**
 * Jarvis WhatsApp Service — OWN DOM DRIVER EDITION
 * -------------------------------------------------
 * No whatsapp-web.js, no venom. Just Puppeteer + our own DOM selectors
 * against live WhatsApp Web. We control everything and fix selectors
 * ourselves when WhatsApp updates their UI.
 *
 * Session: uses a COPY of the user's Chrome profile (chrome_profile_copy)
 * where WhatsApp Web is already logged in. Refresh it with sync_profile.ps1
 * (Chrome must be closed). Env overrides:
 *   CHROME_USER_DATA  - profile folder (default: ./chrome_profile_copy)
 *   CHROME_PROFILE    - profile name   (default: Default)
 *
 * API (same contract as before, so the Python backend is unchanged):
 *   GET  /status             connection state
 *   GET  /qr                 QR info (only when using an unauthenticated profile)
 *   GET  /chats?limit=       chat list (name, preview, time, unread)
 *   GET  /messages?chat=&limit=   recent messages of a chat
 *   POST /send               {to: name|phone, message}
 *   POST /send-file          {to: name|phone, path, caption}
 *   (contacts/chat-info/actions/groups/media: not supported by the DOM driver yet -> 501)
 */
const express = require("express");
const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer");

const PORT = process.env.PORT || 4097;
const PROFILE_DIR = process.env.CHROME_USER_DATA || path.join(__dirname, "chrome_profile_copy");
const PROFILE_NAME = process.env.CHROME_PROFILE || "Default";
const QR_SHOT = path.join(__dirname, "qr_dom.png");

const MEDIA_EXT = /\.(jpe?g|png|gif|webp|bmp|mp4|mov|3gp|mkv)$/i;

// ---------------------------------------------------------------------------
// Browser management
// ---------------------------------------------------------------------------
let browser = null;
let page = null;
let state = "disconnected"; // disconnected | starting | qr | ready
let lastQrAt = 0;

async function launch() {
  if (browser) return;
  state = "starting";
  console.log(`[dom] launching Chrome, profile dir: ${PROFILE_DIR} (${PROFILE_NAME})`);
  browser = await puppeteer.launch({
    headless: "new",
    timeout: 120000,
    channel: "chrome",
    userDataDir: PROFILE_DIR,
    args: [
      "--no-sandbox",
      "--disable-gpu",
      `--profile-directory=${PROFILE_NAME}`,
      "--window-size=1280,900",
      "--no-first-run",
      "--no-default-browser-check",
    ],
    defaultViewport: { width: 1280, height: 900 },
  });
  page = await browser.newPage();
  page.setDefaultTimeout(60000);
  await page.goto("https://web.whatsapp.com", { waitUntil: "domcontentloaded", timeout: 90000 });
  await sleep(8000);
  await refreshState();
  console.log(`[dom] state after boot: ${state}`);
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

// Extract bare phone digits from "digits@c.us", "+92 309..." etc.; null if it's a name.
function phoneDigits(to) {
  const m = String(to).match(/^(\d+)@c\.us$/);
  if (m) return m[1];
  const s = String(to).trim();
  if (/^[+\d][\d\s()-]*$/.test(s)) {
    const d = s.replace(/\D/g, "");
    if (d.length >= 7 && d.length <= 15) return d;
  }
  return null;
}

async function handleTakeoverIfPresent() {
  if (!page) return false;
  try {
    return await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button, [role="button"], div[role="button"]'));
      const useHereBtn = buttons.find(b => b.innerText && b.innerText.toLowerCase().includes("use here"));
      if (useHereBtn) {
        useHereBtn.click();
        return true;
      }
      return false;
    });
  } catch (_) { return false; }
}

async function isLoggedIn() {
  if (!page) return false;
  try {
    // Handle 'Use Here' button if another tab temporarily claimed focus
    const tookOver = await handleTakeoverIfPresent();
    if (tookOver) {
      await sleep(2000);
    }
    return await page.evaluate(() => {
      const pane = document.querySelector("#pane-side");
      return !!pane && pane.innerText.trim().length > 0;
    });
  } catch (_) { return false; }
}

async function refreshState() {
  if (!page) { state = "disconnected"; return state; }
  if (await isLoggedIn()) { state = "ready"; return state; }
  // check for takeover again
  if (await handleTakeoverIfPresent()) {
    await sleep(2000);
    if (await isLoggedIn()) { state = "ready"; return state; }
  }
  // check for QR on the page
  const hasQr = await page.evaluate(() => {
    return document.body.innerText.includes("Link with QR code")
      || !!document.querySelector("canvas[aria-label]");
  }).catch(() => false);
  state = hasQr ? "qr" : "disconnected";
  if (hasQr) {
    await page.screenshot({ path: QR_SHOT });
    lastQrAt = Date.now();
  }
  return state;
}

async function ensureReady() {
  if (!browser) await launch();
  if (state !== "ready") await refreshState();
  if (state === "qr") {
    // refresh QR screenshot at most every 15s
    if (Date.now() - lastQrAt > 15000) {
      await page.reload({ waitUntil: "domcontentloaded" }).catch(() => {});
      await sleep(6000);
      await refreshState();
    }
    const err = new Error(`WhatsApp is not connected (state: qr). Scan ${QR_SHOT} with your phone.`);
    err.status = 409;
    throw err;
  }
  if (state !== "ready") {
    const err = new Error(`WhatsApp is not connected (state: ${state}). Run sync_profile.ps1 or scan the QR.`);
    err.status = 409;
    throw err;
  }
}

// serialize all page operations (one page, one actor at a time)
let chain = Promise.resolve();
function enqueue(fn) {
  const result = chain.then(fn);
  chain = result.catch(() => {});
  return result;
}

// ---------------------------------------------------------------------------
// DOM helpers
// ---------------------------------------------------------------------------
async function openChatByName(name) {
  const needles = [name, name.split(" ")[0]].filter(Boolean);
  for (const needle of needles) {
    // click the search box (current WhatsApp Web uses a plain <input>)
    const searchSel = await firstSelector(page, [
      'input[aria-label="Search or start a new chat"]',
      '[data-testid="chat-list-search-container"] input',
      'input.html-input',
      '[data-testid="search"] input',
    ], 4000);
    if (!searchSel) {
      await page.screenshot({ path: path.join(__dirname, "dbg_search_fail.png") }).catch(() => {});
      throw new Error("Could not find the search box");
    }
    await page.click(searchSel);
    await sleep(300);
    const phoneLike = /^[+0-9()\-\s]+$/.test(needle) && needle.replace(/[^0-9]/g, "").length >= 7;
    const query = phoneLike ? needle.replace(/\s/g, "") : needle;
    // set the value via the native setter + input event: React-controlled inputs
    // re-render on each keystroke and drop focus, so raw keyboard.type loses chars
    await page.evaluate((q, sel) => {
      const input = document.querySelector(sel);
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
      setter.call(input, q);
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }, query, searchSel);
    await sleep(2000);
    // pick result: exact title match first, then substring; click via element handle
    const handles = await page.$$('#pane-side [role="listitem"], #pane-side [data-testid="cell-frame-container"]');
    const titles = await Promise.all(handles.map((h) => h.evaluate((i) =>
      i.getAttribute("title") || i.querySelector("span[title]")?.getAttribute("title") || "")));
    const n = needle.toLowerCase();
    const nd = needle.replace(/[^0-9]/g, "");
    let idx = titles.findIndex((t) => t.trim().toLowerCase() === n);
    if (idx < 0) idx = titles.findIndex((t) => t.toLowerCase().includes(n));
    if (idx < 0 && phoneLike) idx = titles.findIndex((t) => t.replace(/[^0-9]/g, "").includes(nd));
    if (idx >= 0) {
      await handles[idx].click();
      try {
        await page.waitForSelector("#main", { timeout: 8000 });
        await sleep(1500);
        return;
      } catch (_) { /* fall through to next needle */ }
    }
  }
  await page.screenshot({ path: path.join(__dirname, "dbg_chat_open_fail.png") }).catch(() => {});
  throw new Error(`Chat not found: ${name}`);
}

async function firstSelector(pg, selectors, timeoutEach = 3000) {
  for (const sel of selectors) {
    try {
      await pg.waitForSelector(sel, { timeout: timeoutEach });
      return sel;
    } catch (_) { /* try next */ }
  }
  return null;
}

async function clickSendButton() {
  let sel = await firstSelector(page, [
    '[data-testid="send-media"]',
    'button[aria-label*="Send" i]',
    '[data-testid="send"]',
    'button span[data-icon="send"]',
    'footer span[data-icon="send"]',
    'span[data-icon="send"]',
    'div[role="button"][aria-label*="Send" i]',
  ], 3000);
  if (!sel) {
    // fallback: any clickable element labelled "Send" or carrying a send icon
    const clicked = await page.evaluate(() => {
      const els = [...document.querySelectorAll('button, [role="button"], [tabindex]')];
      const target = els.find((e) => {
        const label = (e.getAttribute("aria-label") || "").trim().toLowerCase();
        if (label === "send") return true;
        const icon = e.querySelector("[data-icon]");
        return icon && /send/.test(icon.getAttribute("data-icon") || "");
      });
      if (target) { target.click(); return true; }
      return false;
    });
    if (!clicked) {
      await page.screenshot({ path: path.join(__dirname, "dbg_send_fail.png") }).catch(() => {});
      throw new Error("Send button not found — selectors may need updating");
    }
    return;
  }
  await page.click(sel);
}

async function scrapeChats(limit) {
  return page.evaluate((max) => {
    const items = [...document.querySelectorAll(
      '#pane-side [role="listitem"], #pane-side [data-testid="cell-frame-container"]'
    )].slice(0, max);
    return items.map((el) => {
      const titleEl = el.querySelector("span[title]");
      const name = titleEl ? (titleEl.getAttribute("title") || titleEl.textContent.trim()) : null;
      if (!name) return null;
      const lines = el.innerText.split("\n").map((s) => s.trim()).filter(Boolean);
      const unreadEl = el.querySelector('[data-testid="icon-unread-count"], [aria-label*="unread" i]');
      let unread = 0;
      if (unreadEl) {
        const m = (unreadEl.getAttribute("aria-label") || unreadEl.innerText || "").match(/\d+/);
        unread = m ? parseInt(m[0], 10) : 1;
      }
      return {
        id: name, // DOM driver identifies chats by name
        name,
        preview: lines.length > 1 ? lines.slice(1, 3).join(" ") : "",
        unread,
        isGroup: false,
        pinned: false,
        timestamp: null,
      };
    }).filter(Boolean);
  }, limit);
}

async function scrapeMessages(limit) {
  return page.evaluate((max) => {
    const main = document.querySelector("#main");
    const panelRight = main ? main.getBoundingClientRect().right : 0;
    const bubbles = [...document.querySelectorAll('#main [data-testid="msg-container"]')];
    return bubbles.slice(-max).map((b) => {
      const textEl = b.querySelector(".selectable-text.copyable-text, .selectable-text, [data-testid*='msg-text']");
      // outgoing bubbles hug the right edge of the panel (~57px gap);
      // tick icons no longer have stable data-testids in current WA Web
      const fromMe = panelRight - b.getBoundingClientRect().right < 120;
      return {
        id: null,
        body: textEl ? textEl.innerText : "",
        from: null,
        to: null,
        fromMe,
        timestamp: null,
        type: textEl ? "chat" : "media",
        hasMedia: !textEl,
        caption: null,
        mimetype: null,
        filename: null,
        author: null,
      };
    });
  }, limit);
}

// ---------------------------------------------------------------------------
// Express app
// ---------------------------------------------------------------------------
const app = express();
app.use(express.json({ limit: "50mb" }));
const aw = (fn) => (req, res, next) => fn(req, res, next).catch(next);

app.get("/status", aw(async (req, res) => {
  if (!browser) await launch().catch(() => {});
  else await refreshState();
  res.json({
    state,
    qr: state === "qr" ? `see ${QR_SHOT}` : null,
    qr_image: null,
    pushname: state === "ready" ? PROFILE_NAME : null,
    driver: "dom",
  });
}));

app.get("/qr", aw(async (req, res) => {
  if (!browser) await launch().catch(() => {});
  else await refreshState();
  res.json({ state, qr: state === "qr" ? `see ${QR_SHOT}` : null, qr_image: null });
}));

app.get("/chats", aw(async (req, res) => {
  await ensureReady();
  const limit = Math.min(parseInt(req.query.limit || "50", 10), 200);
  const chats = await enqueue(() => scrapeChats(limit));
  res.json({ chats });
}));

app.get("/messages", aw(async (req, res) => {
  await ensureReady();
  const chat = req.query.chat || "";
  const limit = Math.min(parseInt(req.query.limit || "20", 10), 100);
  const messages = await enqueue(async () => {
    const digits = phoneDigits(chat);
    if (digits) {
      // phone-number chats (incl. the self chat) are not reliably searchable — go direct
      await page.goto(`https://web.whatsapp.com/send?phone=${digits}`,
        { waitUntil: "domcontentloaded", timeout: 90000 });
      await page.waitForSelector("#main", { timeout: 15000 }).catch(() => {});
      await sleep(2500);
    } else {
      await openChatByName(chat);
    }
    return scrapeMessages(limit);
  });
  res.json({ chat: { id: chat, name: chat }, messages });
}));

app.post("/send", aw(async (req, res) => {
  await ensureReady();
  const { to, message } = req.body || {};
  if (!to || !message) return res.status(400).json({ error: "'to' and 'message' are required" });
  const result = await enqueue(async () => {
    const digits = phoneDigits(to);
    if (digits) {
      await page.goto(`https://web.whatsapp.com/send?phone=${digits}&text=${encodeURIComponent(String(message))}`,
        { waitUntil: "domcontentloaded", timeout: 90000 });
      await sleep(5000);
    } else {
      await openChatByName(String(to));
      const boxSel = await firstSelector(page, [
        '[data-testid="conversation-compose-box-input"]',
        'footer div[contenteditable="true"]',
        'div[contenteditable="true"][data-tab="10"]',
        'div[contenteditable="true"][role="textbox"]',
      ], 5000);
      if (!boxSel) throw new Error("Message compose box not found");
      await page.click(boxSel);
      await page.keyboard.type(String(message), { delay: 5 });
      await sleep(500);
    }
    await clickSendButton();
    await sleep(2500);
    return { to: String(to) };
  });
  res.json({ sent: true, to: result.to, messageId: null });
}));

app.post("/send-file", aw(async (req, res) => {
  await ensureReady();
  const { to, path: filePath, caption } = req.body || {};
  if (!to || !filePath) return res.status(400).json({ error: "'to' and 'path' are required" });
  const abs = path.resolve(filePath);
  if (!fs.existsSync(abs)) return res.status(400).json({ error: `File not found: ${abs}` });

  const result = await enqueue(async () => {
    const digits = phoneDigits(to);
    if (digits) {
      await page.goto(`https://web.whatsapp.com/send?phone=${digits}`,
        { waitUntil: "domcontentloaded", timeout: 90000 });
      await sleep(5000);
    } else {
      await openChatByName(String(to));
    }

    const isMedia = MEDIA_EXT.test(abs);
    // WA creates the file input dynamically at menu-click time (it is removed
    // once the native dialog closes), so we intercept the native file chooser
    // instead of hunting for a hidden input in the DOM.
    const attachSel = await firstSelector(page, [
      '[data-testid="clip"]',
      'span[data-icon="plus"]',
      '[title="Attach"]',
      'button[aria-label*="Attach" i]',
      '[aria-label*="attach" i]',
    ], 5000);
    if (!attachSel) throw new Error("Attach button not found");
    await page.click(attachSel);
    await sleep(800);
    const menuRe = isMedia
      ? /^(photos|photos & videos|photos and videos)$/i
      : /^document$/i;
    const handles = await page.$$('li[role="button"], [role="menuitem"], li, [role="button"]');
    let itemHandle = null;
    for (const h of handles) {
      const txt = await h.evaluate((e) => (e.innerText || "").trim());
      if (menuRe.test(txt) && await h.isIntersectingViewport()) { itemHandle = h; break; }
    }
    if (!itemHandle) throw new Error(`Attach menu item not found (media=${isMedia})`);
    const [chooser] = await Promise.all([
      page.waitForFileChooser({ timeout: 15000 }),
      itemHandle.click(),
    ]);
    await chooser.accept([abs]);
    await sleep(4000);

    if (caption) {
      const capSel = await firstSelector(page, [
        '[data-testid="media-caption-input"]',
        'div[contenteditable="true"][data-tab="10"]',
        'div[contenteditable="true"][role="textbox"]',
      ], 4000);
      if (capSel) { await page.click(capSel); await page.keyboard.type(String(caption), { delay: 5 }); }
    }
    await clickSendButton();
    await sleep(2500);
    return { to: String(to), filename: path.basename(abs) };
  });
  res.json({ sent: true, to: result.to, messageId: null, filename: result.filename });
}));

// Not supported by the DOM driver (yet) — kept for API contract compatibility
const notSupported = (what) => (req, res) =>
  res.status(501).json({ error: `${what} is not supported by the DOM driver yet` });
app.get("/contacts", notSupported("contacts"));
app.get("/chat-info", notSupported("chat-info"));
app.post("/chat/action", notSupported("chat actions (pin/mute/archive)"));
app.post("/group", notSupported("group management"));
app.get("/media", notSupported("media download"));

// error handler
app.use((err, req, res, next) => {
  const status = err.status || 500;
  console.error("[whatsapp-service] error:", err.message);
  res.status(status).json({ error: err.message || String(err) });
});

app.listen(PORT, () => {
  console.log(`[whatsapp-service] DOM driver listening on http://127.0.0.1:${PORT}`);
});

// boot the browser in the background
launch().catch((err) => console.error("[dom] launch failed:", err.message));
