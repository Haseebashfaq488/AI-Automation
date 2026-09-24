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
  console.log("[dom] navigating to https://web.whatsapp.com...");
  await page.goto("https://web.whatsapp.com", { waitUntil: "domcontentloaded", timeout: 90000 });

  // Keep checking in a loop until state is 'ready' or 'qr'
  console.log("[dom] waiting for WhatsApp Web session to reach 'ready' state...");
  let attempt = 1;
  while (true) {
    await sleep(5000);
    await refreshState();
    console.log(`[dom] boot check attempt #${attempt}: state = ${state}`);
    if (state === "ready") {
      console.log(`[dom] WhatsApp Web connected successfully! State after boot: ready`);
      break;
    }
    if (state === "qr") {
      console.log(`[dom] WhatsApp Web requires QR code scan. Screenshot saved to ${QR_SHOT}`);
      break;
    }
    // Every 30 seconds if still disconnected, reload the page to refresh connection
    if (attempt % 6 === 0) {
      console.log("[dom] still disconnected after 30s, reloading WhatsApp Web page...");
      await page.reload({ waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
    }
    attempt++;
  }
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
  if (!name) throw new Error("Chat name is required");
  const cleanName = name.trim();
  const lowerName = cleanName.toLowerCase();
  const asciiName = cleanName.replace(/[^\w\s]/g, "").trim().toLowerCase();

  // 1. Check visible chats in #pane-side directly first (fast & reliable)
  const handles = await page.$$('#pane-side [role="listitem"], #pane-side [data-testid="cell-frame-container"]');
  for (const h of handles) {
    const title = await h.evaluate((i) => {
      const span = i.querySelector("span[title]");
      return span ? (span.getAttribute("title") || span.textContent.trim()) : (i.getAttribute("title") || i.innerText || "");
    });
    const tLower = title.trim().toLowerCase();
    const tAscii = tLower.replace(/[^\w\s]/g, "").trim();

    if (tLower === lowerName || (lowerName && tLower.includes(lowerName)) || (asciiName && tAscii.includes(asciiName))) {
      await h.click();
      try {
        await page.waitForSelector("#main", { timeout: 6000 });
        await sleep(1000);
        return;
      } catch (_) {}
    }
  }

  // 2. Search fallback
  const needles = [cleanName, cleanName.split(" ")[0], asciiName].filter(Boolean);
  for (const needle of needles) {
    const searchSel = await firstSelector(page, [
      'input[aria-label="Search or start a new chat"]',
      '[data-testid="chat-list-search-container"] input',
      'input.html-input',
      '[data-testid="search"] input',
    ], 3000);

    if (searchSel) {
      await page.click(searchSel);
      await sleep(200);

      // Clear search box first
      await page.evaluate((sel) => {
        const input = document.querySelector(sel);
        if (input) {
          const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
          setter.call(input, "");
          input.dispatchEvent(new Event("input", { bubbles: true }));
        }
      }, searchSel);

      await sleep(200);

      const phoneLike = /^[+0-9()\-\s]+$/.test(needle) && needle.replace(/[^0-9]/g, "").length >= 7;
      const query = phoneLike ? needle.replace(/\s/g, "") : needle;

      await page.evaluate((q, sel) => {
        const input = document.querySelector(sel);
        if (input) {
          const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
          setter.call(input, q);
          input.dispatchEvent(new Event("input", { bubbles: true }));
        }
      }, query, searchSel);

      await sleep(2000);

      const searchHandles = await page.$$('#pane-side [role="listitem"], #pane-side [data-testid="cell-frame-container"]');
      for (const h of searchHandles) {
        const title = await h.evaluate((i) => {
          const span = i.querySelector("span[title]");
          return span ? (span.getAttribute("title") || span.textContent.trim()) : (i.getAttribute("title") || i.innerText || "");
        });
        const tLower = title.trim().toLowerCase();
        const nLower = needle.toLowerCase();
        if (tLower === nLower || tLower.includes(nLower)) {
          await h.click();
          try {
            await page.waitForSelector("#main", { timeout: 8000 });
            await sleep(1500);
            return;
          } catch (_) {}
        }
      }
    }
  }

  // Clear search on exit
  await page.keyboard.press("Escape").catch(() => {});
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

function classifyTimestamp(timeStr) {
  if (!timeStr) return { bucket: "today", is_within_3_days: true };
  const s = timeStr.trim().toLowerCase();

  // Time format e.g. "10:30 AM", "9:50", "14:20", "11:24 am" -> Today
  if (/^\d{1,2}:\d{2}(\s*[ap]m)?$/i.test(s)) {
    return { bucket: "today", is_within_3_days: true };
  }

  // "Yesterday" -> Yesterday
  if (s === "yesterday") {
    return { bucket: "yesterday", is_within_3_days: true };
  }

  // Day names check (relative to current day of week)
  const daysOfWeek = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
  const now = new Date();
  const todayDay = daysOfWeek[now.getDay()];
  const yesterdayDay = daysOfWeek[(now.getDay() + 6) % 7];
  const dayBeforeYesterday = daysOfWeek[(now.getDay() + 5) % 7];

  if (s === dayBeforeYesterday) {
    return { bucket: "day_before_yesterday", is_within_3_days: true };
  }
  if (s === yesterdayDay || s === todayDay) {
    return { bucket: "yesterday", is_within_3_days: true };
  }

  // Check if date format M/D/YYYY or D/M/YYYY
  const dateMatch = s.match(/^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})$/);
  if (dateMatch) {
    let p1 = parseInt(dateMatch[1], 10);
    let p2 = parseInt(dateMatch[2], 10);
    const y = parseInt(dateMatch[3].length === 2 ? "20" + dateMatch[3] : dateMatch[3], 10);

    let m, d;
    if (p1 <= 12 && p2 > 12) {
      // M/D/YYYY
      m = p1 - 1;
      d = p2;
    } else if (p1 > 12 && p2 <= 12) {
      // D/M/YYYY
      d = p1;
      m = p2 - 1;
    } else {
      // Default to M/D/YYYY for standard WhatsApp Web English UI
      m = p1 - 1;
      d = p2;
    }

    const msgDate = new Date(y, m, d);
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const diffDays = Math.round((todayStart - new Date(y, m, d)) / (1000 * 60 * 60 * 24));
    if (diffDays === 0) return { bucket: "today", is_within_3_days: true };
    if (diffDays === 1) return { bucket: "yesterday", is_within_3_days: true };
    if (diffDays === 2) return { bucket: "day_before_yesterday", is_within_3_days: true };
    return { bucket: "older", is_within_3_days: false };
  }

  return { bucket: "older", is_within_3_days: false };
}

async function toggleUnreadFilter(enable) {
  if (!page) return false;
  return page.evaluate((shouldEnable) => {
    const candidates = [
      ...document.querySelectorAll('button, div[role="button"], span[role="button"], [data-testid*="filter"], [aria-label*="unread" i], [title*="unread" i], [aria-label*="all" i], [title*="all" i]')
    ];
    
    if (shouldEnable) {
      const unreadBtn = candidates.find((el) => {
        const text = (el.innerText || "").trim().toLowerCase();
        const label = (el.getAttribute("aria-label") || el.getAttribute("title") || "").trim().toLowerCase();
        return text.startsWith("unread") || label.startsWith("unread") || label.includes("filter unread") || label.includes("unread chats");
      });
      if (unreadBtn) {
        unreadBtn.click();
        return true;
      }
    } else {
      // Restore all chats by clicking "All" button
      const allBtn = candidates.find((el) => {
        const text = (el.innerText || "").trim().toLowerCase();
        const label = (el.getAttribute("aria-label") || el.getAttribute("title") || "").trim().toLowerCase();
        return text === "all" || text.startsWith("all") || label === "all" || label.startsWith("all");
      });
      if (allBtn) {
        allBtn.click();
        return true;
      }
    }
    return false;
  }, enable);
}

async function scrapeChats(limit = 50, days = 3) {
  // Reset scroll to top so top chats (Today/Yesterday) are in DOM view
  await page.evaluate(() => {
    const pane = document.querySelector("#pane-side");
    if (pane) pane.scrollTop = 0;
  });
  await sleep(400);

  const rawChats = await page.evaluate((max) => {
    const pane = document.querySelector("#pane-side");
    if (!pane) return [];

    // Target individual chat cell containers only (no parent list containers)
    let rows = [...pane.querySelectorAll('[data-testid="cell-frame-container"]')];
    if (rows.length === 0) {
      rows = [...pane.querySelectorAll('div[role="listitem"]')];
    }
    if (rows.length === 0) {
      // Fallback to direct cell children
      rows = [...pane.querySelectorAll('div[tabindex="-1"] > div')].filter((el) => {
        return !!el.querySelector('span[title]');
      });
    }

    const seenNames = new Set();
    const chats = [];

    for (const el of rows) {
      // Chat title is strictly inside the cell's header span
      const titleEl = el.querySelector('span[title]');
      let name = titleEl ? (titleEl.getAttribute('title') || titleEl.innerText || "").trim() : null;

      if (!name) {
        const autoSpan = el.querySelector('div[class*="_ak8q"] span, span[dir="auto"]');
        if (autoSpan) name = autoSpan.innerText.trim();
      }

      if (!name || seenNames.has(name)) continue;

      // Extract time / date label
      let timeStr = null;
      const timeRegex = /^(\d{1,2}:\d{2}(\s*[ap]m)?|yesterday|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})$/i;
      
      const allSpans = [...el.querySelectorAll('span, div')];
      for (const sp of allSpans) {
        const txt = sp.innerText ? sp.innerText.trim() : "";
        if (txt && timeRegex.test(txt) && txt !== name) {
          timeStr = txt;
          break;
        }
      }

      // Extract unread badge
      const unreadEl = el.querySelector('[data-testid="icon-unread-count"], [aria-label*="unread" i], span[aria-label*="unread"]');
      let unread = 0;
      if (unreadEl) {
        const m = (unreadEl.getAttribute("aria-label") || unreadEl.innerText || "").match(/\d+/);
        unread = m ? parseInt(m[0], 10) : 1;
      }

      // Extract preview (subtitle)
      let preview = "";
      const previewEl = el.querySelector('div[class*="_ak8k"], div[class*="_ak8l"], span[data-testid="last-msg-status"]');
      if (previewEl) {
        preview = previewEl.innerText.trim();
      } else {
        const lines = el.innerText.split("\n").map((s) => s.trim()).filter((s) => s && s !== name && s !== timeStr && s !== String(unread));
        preview = lines.join(" ");
      }

      const hasGroupIcon = !!el.querySelector('[data-testid="group"], [data-icon*="group"], [data-icon*="community"]');
      const isGroup = hasGroupIcon || preview.includes(":") || name.includes("(") || name.includes("Batch") || name.includes("2026");

      seenNames.add(name);
      chats.push({
        id: name,
        name,
        preview: preview.slice(0, 150),
        unread,
        isGroup,
        pinned: !!el.querySelector('[data-testid="pinned"], [data-icon="pinned"]'),
        timestamp: timeStr,
      });

      if (chats.length >= max) break;
    }

    return chats;
  }, limit);

  return rawChats.map((c) => {
    const classification = classifyTimestamp(c.timestamp);
    return {
      ...c,
      activity_bucket: classification.bucket,
      is_within_3_days: classification.is_within_3_days,
    };
  }).filter((c) => {
    if (days === 3) return c.is_within_3_days;
    return true;
  });
}

async function scrapeMessagesWithDates(limit = 30, maxDays = 3) {
  return page.evaluate((max, daysLimit) => {
    const main = document.querySelector("#main");
    if (!main) return [];
    const panelRight = main.getBoundingClientRect().right;

    const daysOfWeek = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"];
    const now = new Date();
    const dayBeforeYesterdayDayName = daysOfWeek[(now.getDay() + 5) % 7];
    const yesterdayDayName = daysOfWeek[(now.getDay() + 6) % 7];
    const todayDayName = daysOfWeek[now.getDay()];

    let currentDateCategory = "Today";

    // Scan all message containers and date dividers in chronological order
    const nodes = [...main.querySelectorAll('[data-testid="msg-container"], div[role="row"], div[class*="focusable-list-item"]')];
    const results = [];
    const seenKeys = new Set();

    for (const node of nodes) {
      const textContent = node.innerText ? node.innerText.trim() : "";
      const isMsg = node.matches('[data-testid="msg-container"]') || !!node.querySelector('[data-testid="msg-container"]');

      // Date divider detection
      if (!isMsg && textContent.length > 0 && textContent.length < 35) {
        if (/^TODAY$/i.test(textContent)) {
          currentDateCategory = "Today";
          continue;
        } else if (/^YESTERDAY$/i.test(textContent)) {
          currentDateCategory = "Yesterday";
          continue;
        } else if (textContent.toLowerCase() === dayBeforeYesterdayDayName) {
          currentDateCategory = "Day Before Yesterday";
          continue;
        } else if (daysOfWeek.includes(textContent.toLowerCase())) {
          currentDateCategory = textContent;
          continue;
        } else if (/^\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}$/.test(textContent) || /^[A-Z]+ \d{1,2}, \d{4}$/i.test(textContent)) {
          currentDateCategory = textContent;
          continue;
        }
      }

      const b = node.matches('[data-testid="msg-container"]') ? node : node.querySelector('[data-testid="msg-container"]');
      if (!b) continue;

      const textEl = b.querySelector(".selectable-text.copyable-text, .selectable-text, [data-testid*='msg-text']");
      const copyable = b.querySelector(".copyable-text");
      const preText = copyable ? copyable.getAttribute("data-pre-plain-text") : null;

      let author = null;
      let timeStr = null;
      if (preText) {
        const m = preText.match(/\[(.*?)(?:,\s*(.*?))?\]\s*([^:]+):?/);
        if (m) {
          timeStr = m[1] + (m[2] ? ` ${m[2]}` : "");
          author = m[3] ? m[3].trim() : null;
        }
      }

      if (!author) {
        const authorEl = b.querySelector('[data-testid="author-name"], span._ak8i, span[dir="auto"]');
        if (authorEl && !b.querySelector('.selectable-text')?.contains(authorEl)) {
          author = authorEl.innerText.trim();
        }
      }

      if (!timeStr) {
        const metaEl = b.querySelector('[data-testid="msg-meta"], div[class*="_amjz"], span[class*="_amjz"]');
        if (metaEl) {
          timeStr = metaEl.innerText.trim();
        }
      }

      const fromMe = panelRight - b.getBoundingClientRect().right < 120;
      const bodyText = textEl ? textEl.innerText.trim() : "";

      // Deduplicate identical bubbles
      const itemKey = `${fromMe ? 'me' : (author || 'anon')}_${timeStr || ''}_${bodyText || 'media'}`;
      if (seenKeys.has(itemKey)) continue;
      seenKeys.add(itemKey);

      // Classify whether message is within Today, Yesterday, or Day Before Yesterday
      const allowedCategories = ["Today", "Yesterday", "Day Before Yesterday", todayDayName, yesterdayDayName, dayBeforeYesterdayDayName];
      const isWithinDays = allowedCategories.some((c) => c.toLowerCase() === currentDateCategory.toLowerCase());

      results.push({
        id: null,
        body: bodyText,
        from: fromMe ? "You" : author,
        to: null,
        fromMe,
        date: currentDateCategory,
        time: timeStr || "Recent",
        timestamp: `${currentDateCategory} ${timeStr || ''}`.trim(),
        type: textEl ? "chat" : "media",
        hasMedia: !textEl,
        caption: null,
        mimetype: null,
        filename: null,
        author: author || (fromMe ? "You" : null),
        is_within_days: isWithinDays,
      });
    }

    const filtered = (daysLimit === 3 ? results.filter((r) => r.is_within_days) : results);
    return (filtered.length > 0 ? filtered : results).slice(-max);
  }, limit, maxDays);
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
  const days = req.query.days ? parseInt(req.query.days, 10) : 3;
  const unreadOnly = req.query.unread_only === "true" || req.query.unread_only === "1";

  const chats = await enqueue(async () => {
    if (unreadOnly) {
      const toggled = await toggleUnreadFilter(true);
      if (toggled) await sleep(1200);
      let list = await scrapeChats(limit, null);
      if (toggled) {
        await toggleUnreadFilter(false);
        await sleep(600);
      }
      return list.filter((c) => c.unread > 0 || toggled);
    }
    return scrapeChats(limit, days);
  });
  res.json({ chats });
}));

app.get("/messages", aw(async (req, res) => {
  await ensureReady();
  const chat = req.query.chat || "";
  const limit = Math.min(parseInt(req.query.limit || "30", 10), 100);
  const days = req.query.days ? parseInt(req.query.days, 10) : 3;

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
    return scrapeMessagesWithDates(limit, days);
  });
  res.json({ chat: { id: chat, name: chat }, messages });
}));

app.get("/conversations/recent", aw(async (req, res) => {
  await ensureReady();
  const chatLimit = Math.min(parseInt(req.query.chat_limit || "8", 10), 20);
  const msgLimit = Math.min(parseInt(req.query.messages_per_chat || "10", 10), 30);
  const days = req.query.days ? parseInt(req.query.days, 10) : 3;

  const conversations = await enqueue(async () => {
    const activeChats = await scrapeChats(chatLimit, days);
    const results = [];

    for (const c of activeChats) {
      const chatName = c.name;
      try {
        const digits = phoneDigits(chatName);
        if (digits) {
          await page.goto(`https://web.whatsapp.com/send?phone=${digits}`,
            { waitUntil: "domcontentloaded", timeout: 90000 });
          await page.waitForSelector("#main", { timeout: 15000 }).catch(() => {});
          await sleep(2000);
        } else {
          await openChatByName(chatName);
        }

        const msgs = await scrapeMessagesWithDates(msgLimit, days);
        results.push({
          ...c,
          messages: msgs,
        });
      } catch (err) {
        results.push({
          ...c,
          messages: [],
          error: err.message,
        });
      }
    }
    return results;
  });

  res.json({ count: conversations.length, conversations });
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

// background health check to auto-recover if state ever drops
setInterval(async () => {
  if (page && state !== "ready" && state !== "qr" && state !== "starting") {
    try {
      await enqueue(async () => {
        await refreshState();
        if (state === "ready") {
          console.log("[dom] background auto-recovery: state is now READY!");
        }
      });
    } catch (_) {}
  }
}, 15000);

