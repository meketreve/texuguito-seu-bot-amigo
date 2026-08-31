# LPC Pixel-Art Avatars Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace chat-parade's procedurally-generated pixel avatars with real Liberated Pixel Cup (LPC) sprites — real walk-cycle animation, layered hat/accessory sprites, and free-form `!cor` recoloring done at runtime in the browser via canvas.

**Architecture:** The Python side gets simpler: `chat_parade/avatar.py` is deleted, and `web_server.py` just forwards a viewer's raw `cor`/`chapeu`/`acessorio` fields instead of pre-rendering a pixel grid. All the new complexity moves to `web/overlay.js`, which loads a handful of pre-sourced LPC PNG spritesheets (already committed to the repo), slices out walk-cycle frames, composites them in the right layer order (wings-behind, tinted body, hat, accessory, wings-in-front), and recolors the body layer at runtime via a desaturate + canvas `multiply` blend, cached per (frame, color) so nothing is retinted twice.

**Tech Stack:** Python/FastAPI (unchanged), vanilla JS + Canvas 2D (`multiply`/`destination-in` composite operations, `getImageData`/`putImageData`), pre-sourced LPC PNG assets already in `web/assets/lpc/`.

**Spec:** [docs/superpowers/specs/2026-08-30-lpc-pixelart-avatars-design.md](../specs/2026-08-30-lpc-pixelart-avatars-design.md) (supersedes only the avatar-rendering section of [docs/superpowers/specs/2026-08-30-chat-parade-design.md](../specs/2026-08-30-chat-parade-design.md); chat commands, persistence, and Twitch integration are unchanged and out of scope for this plan)

## Global Constraints

- The `cor`/`chapeu`/`acessorio` fields on `Viewer` (in `viewer_store.py`) do not change — this plan only changes how they're *rendered*, never their schema, validation, or the chat commands that set them.
- All LPC assets are already downloaded, verified (visually and by PNG header), and committed at `web/assets/lpc/*.png` + `web/assets/lpc/manifest.json` — no task in this plan re-downloads or re-sources assets.
- Sheet geometry (from `manifest.json`, already correct, do not re-derive): 576x256px, 9 columns x 4 rows, 64x64px per cell. `direction_row.right = 3`. `walk_frame_columns = [1,2,3,4,5,6,7,8]` (column 0 is a standing pose, unused).
- Only the composed `body_walk.png` + `head_walk.png` layer is tinted by `!cor`. `chapeu` and `acessorio` sprites always draw in their original, un-tinted color.
- Only the `right`-facing row is ever loaded/sliced. The `left`-facing look is the same frames mirrored via `ctx.scale(-1, 1)` — there is no separate left-facing asset and none should be added.
- No pytest coverage is expected or required for `web/overlay.js` — this codebase's established convention (see prior commits touching this file) is a standalone Node.js verification script (`vm.runInContext`, stub `document`/`window`/`performance`/canvas methods) run manually during the task, not a permanent test file. The Python side (Task 1) is TDD'd with pytest as usual.

---

### Task 1: Server sends raw viewer fields instead of a rendered pixel grid

**Files:**
- Delete: `chat_parade/avatar.py`
- Delete: `tests/test_avatar.py`
- Modify: `chat_parade/web_server.py:1-33` (imports + `viewer_payload`)
- Modify: `tests/test_web_server.py` (add one regression test)

**Interfaces:**
- Consumes: `chat_parade.viewer_store.ViewerStore.get_or_create`, `.status_for` (unchanged, from the original plan).
- Produces: `chat_parade.web_server.viewer_payload(store, username) -> dict` now returns `{"username", "nick", "cor", "chapeu", "acessorio", "is_mod", "is_sub", "is_broadcaster", "dance_remaining", "cheer_remaining"}` — no `"grid"` key. `chapeu`/`acessorio` may be `None`. This is the exact shape Task 2's `overlay.js` consumes.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_web_server.py`, right after `test_payload_remaining_is_zero_once_the_animation_expired`:

```python
def test_payload_sends_raw_cor_chapeu_acessorio_not_a_grid(tmp_path):
    """Regression test: the client now renders real sprites from these three
    raw fields directly; a pre-rendered pixel grid is no longer part of the
    contract, and re-adding one would be dead weight sent over every
    broadcast."""
    store = ViewerStore(tmp_path / "v.json")
    store.set_color("fulano", "#ff8800")
    store.set_chapeu("fulano", "coroa")
    store.set_acessorio("fulano", "asas")

    payload = viewer_payload(store, "fulano")

    assert payload["cor"] == "#ff8800"
    assert payload["chapeu"] == "coroa"
    assert payload["acessorio"] == "asas"
    assert "grid" not in payload
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_web_server.py::test_payload_sends_raw_cor_chapeu_acessorio_not_a_grid -v`
Expected: FAIL — `AssertionError: assert '#ff8800' == [[...pixel grid...]]` (or similar), since `viewer_payload` still sends `"grid"` and not `"cor"`.

- [ ] **Step 3: Update `viewer_payload` and remove the avatar import**

In `chat_parade/web_server.py`, delete the import line:

```python
from chat_parade.avatar import build_avatar_grid
```

Replace the `viewer_payload` function body:

```python
def viewer_payload(store: ViewerStore, username: str) -> dict[str, Any]:
    viewer = store.get_or_create(username)
    status = store.status_for(username)
    return {
        "username": username,
        "nick": viewer.nick or username,
        "cor": viewer.cor,
        "chapeu": viewer.chapeu,
        "acessorio": viewer.acessorio,
        "is_mod": status.is_mod,
        "is_sub": status.is_sub,
        "is_broadcaster": status.is_broadcaster,
        # Seconds remaining, not a boolean: the client turns these into its own
        # deadlines and re-checks them every frame. A boolean computed here would
        # stay true on the client until the next broadcast happened to arrive.
        "dance_remaining": max(0.0, status.dancing_until - time.time()),
        "cheer_remaining": max(0.0, status.cheer_until - time.time()),
    }
```

- [ ] **Step 4: Delete the now-unused avatar module and its test**

```bash
rm chat_parade/avatar.py tests/test_avatar.py
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `pytest tests/test_web_server.py::test_payload_sends_raw_cor_chapeu_acessorio_not_a_grid -v`
Expected: PASS.

- [ ] **Step 6: Run the full suite**

Run: `pytest -v`
Expected: PASS — every remaining test green (avatar.py's own tests are gone since the module is gone; nothing else imported it besides `web_server.py`).

- [ ] **Step 7: Commit**

```bash
git add chat_parade/web_server.py tests/test_web_server.py
git rm chat_parade/avatar.py tests/test_avatar.py
git commit -m "Send raw cor/chapeu/acessorio instead of a rendered pixel grid"
```

---

### Task 2: Sprite-based rendering in the overlay

**Files:**
- Modify: `web/overlay.js` (full rewrite of the drawing/state pipeline; direction, speed, bounce, dance/cheer, connect/WebSocket logic all carry over unchanged)

**Interfaces:**
- Consumes: `chat_parade.web_server.viewer_payload`'s new shape from Task 1 (`cor`, `chapeu`, `acessorio` instead of `grid`), served over the existing `/ws` WebSocket. `web/assets/lpc/manifest.json` and the PNGs it references, served by the existing `/static` mount (`GET /static/lpc/manifest.json`, `GET /static/lpc/<filename>`).
- Produces: nothing consumed elsewhere in the codebase — `overlay.js` is the leaf of the render pipeline.

This task has no automated test suite (see Global Constraints). Verify each step with the throwaway Node.js harness in Step 6 — write it once, run it after every code change in Steps 1-5, discard it at the end (do not commit it).

- [ ] **Step 1: Replace the whole file**

Replace the full contents of `web/overlay.js` with:

```javascript
const SPEED_PX_PER_SEC = 60;
const SPEED_MIN_FACTOR = 0.75;
const SPEED_SPREAD_FACTOR = 0.5;
const PIXELS_PER_WALK_FRAME = 8;

const canvas = document.getElementById("parade");
const ctx = canvas.getContext("2d");

const viewers = new Map();

let manifest = null;
// Fallback until manifest.json loads; matches the real sprite size (64x64),
// so layout math run before the fetch resolves is already correct.
let frameWidth = 64;
let frameHeight = 64;

const imageCache = new Map(); // filename -> HTMLImageElement
const shadingMaskCache = new Map(); // frameColumn -> HTMLCanvasElement (grayscale)
const tintCache = new Map(); // "frameColumn|color" -> HTMLCanvasElement (tinted)

function loadImage(filename) {
  let img = imageCache.get(filename);
  if (!img) {
    img = new Image();
    img.src = `/static/assets/lpc/${filename}`;
    imageCache.set(filename, img);
  }
  return img;
}

async function loadManifest() {
  const response = await fetch("/static/assets/lpc/manifest.json");
  manifest = await response.json();
  frameWidth = manifest.frame_width;
  frameHeight = manifest.frame_height;

  for (const layer of manifest.base_layers) loadImage(layer);
  for (const file of Object.values(manifest.hats)) loadImage(file);
  for (const file of Object.values(manifest.accessories)) loadImage(file);
  loadImage(manifest.wings.bg);
  loadImage(manifest.wings.fg);
}

// True once every asset the manifest lists has actually finished loading.
// Guards getShadingMask/getTintedBase: reading getImageData from a canvas
// that drew an unloaded image returns blank pixels, and caching that would
// permanently strand a viewer as invisible even after the image loads.
function assetsReady() {
  if (!manifest) return false;
  for (const img of imageCache.values()) {
    if (!img.complete || img.naturalWidth === 0) return false;
  }
  return true;
}

function laneY() {
  return canvas.height - frameHeight - 10;
}

// The OBS Browser Source can be any size the streamer picks, so track the
// window instead of assuming a hardcoded size. laneY() and randomX() both
// derive from the canvas dimensions, so they adapt on their own; existing
// viewers keep a y captured at upsert time, so re-seat them onto the new lane.
function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  const y = laneY();
  for (const viewer of viewers.values()) {
    viewer.y = y;
  }
}

function randomX(width) {
  return Math.random() * Math.max(0, canvas.width - width);
}

// Deterministic per-username initial walking direction, same idea as the
// server's old seeded avatar shape: same username always starts the same way.
function hashUsername(username) {
  let hash = 0;
  for (let i = 0; i < username.length; i++) {
    hash = (hash * 31 + username.charCodeAt(i)) | 0;
  }
  return hash;
}

function initialDirection(username) {
  return hashUsername(username) % 2 === 0 ? 1 : -1;
}

// Deterministic per-username speed, used only for the initial spawn.
function individualSpeed(username) {
  const spread = Math.abs(hashUsername(username + "speed")) % 100;
  return SPEED_PX_PER_SEC * (SPEED_MIN_FACTOR + (spread / 100) * SPEED_SPREAD_FACTOR);
}

// Genuinely random speed, re-rolled every time a viewer bounces off an edge.
function randomSpeed() {
  return SPEED_PX_PER_SEC * (SPEED_MIN_FACTOR + Math.random() * SPEED_SPREAD_FACTOR);
}

function upsertViewer(payload) {
  const existing = viewers.get(payload.username);
  const x = existing ? existing.x : randomX(frameWidth);
  const direction = existing ? existing.direction : initialDirection(payload.username);
  const speed = existing ? existing.speed : individualSpeed(payload.username);
  const distanceWalked = existing ? existing.distanceWalked : 0;
  // The server sends seconds remaining, not booleans: turn them into absolute
  // deadlines on the same clock tick() uses so drawViewer can re-check them
  // every frame instead of latching a stale boolean until the next broadcast.
  const now = performance.now();
  viewers.set(payload.username, {
    ...payload,
    x,
    y: laneY(),
    direction,
    speed,
    distanceWalked,
    danceUntil: now + (payload.dance_remaining || 0) * 1000,
    cheerUntil: now + (payload.cheer_remaining || 0) * 1000,
  });
}

function removeViewer(username) {
  viewers.delete(username);
}

function applySnapshot(snapshot) {
  viewers.clear();
  for (const viewer of snapshot.viewers) {
    upsertViewer(viewer);
  }
}

function connect() {
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const ws = new WebSocket(`${protocol}//${location.host}/ws`);

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === "snapshot") {
      applySnapshot(message);
    } else if (message.type === "left") {
      removeViewer(message.username);
    } else {
      upsertViewer(message.viewer);
    }
  };

  ws.onclose = () => {
    setTimeout(connect, 1000);
  };
}

// --- Sprite composition ---

function walkFrameColumn(distanceWalked) {
  const columns = manifest.walk_frame_columns;
  const step = Math.floor(distanceWalked / PIXELS_PER_WALK_FRAME) % columns.length;
  return columns[step];
}

// Grayscale (luminance) render of the composed body+head layer for one walk
// frame. This is the reusable "shading" that getTintedBase multiplies an
// arbitrary color against — computed once per frame column, not per viewer.
function getShadingMask(frameColumn) {
  let mask = shadingMaskCache.get(frameColumn);
  if (mask) return mask;

  mask = document.createElement("canvas");
  mask.width = frameWidth;
  mask.height = frameHeight;
  const mctx = mask.getContext("2d");

  const sx = frameColumn * frameWidth;
  const sy = manifest.direction_row.right * frameHeight;

  for (const layer of manifest.base_layers) {
    mctx.drawImage(loadImage(layer), sx, sy, frameWidth, frameHeight, 0, 0, frameWidth, frameHeight);
  }

  const imageData = mctx.getImageData(0, 0, frameWidth, frameHeight);
  const data = imageData.data;
  for (let i = 0; i < data.length; i += 4) {
    const luminance = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
    data[i] = luminance;
    data[i + 1] = luminance;
    data[i + 2] = luminance;
    // data[i + 3] (alpha) is left untouched.
  }
  mctx.putImageData(imageData, 0, 0);

  shadingMaskCache.set(frameColumn, mask);
  return mask;
}

// Body+head tinted to `color`, cached per (frameColumn, color) so no combo is
// ever recomputed. "multiply" against the grayscale mask approximates the
// target color while keeping the sprite's shading; "destination-in" restores
// the transparency multiply would otherwise flatten to opaque everywhere.
function getTintedBase(frameColumn, color) {
  const key = `${frameColumn}|${color}`;
  let tinted = tintCache.get(key);
  if (tinted) return tinted;

  const mask = getShadingMask(frameColumn);

  tinted = document.createElement("canvas");
  tinted.width = frameWidth;
  tinted.height = frameHeight;
  const tctx = tinted.getContext("2d");

  tctx.drawImage(mask, 0, 0);
  tctx.globalCompositeOperation = "multiply";
  tctx.fillStyle = color;
  tctx.fillRect(0, 0, frameWidth, frameHeight);
  tctx.globalCompositeOperation = "destination-in";
  tctx.drawImage(mask, 0, 0);
  tctx.globalCompositeOperation = "source-over";

  tintCache.set(key, tinted);
  return tinted;
}

function drawSpriteLayer(image, frameColumn, x, y) {
  const sx = frameColumn * frameWidth;
  const sy = manifest.direction_row.right * frameHeight;
  ctx.drawImage(image, sx, sy, frameWidth, frameHeight, x, y, frameWidth, frameHeight);
}

// Draws one fully-composed viewer at (x, y) in the CURRENT ctx transform.
// Layer order: wings-behind, tinted body, hat, accessory, wings-in-front —
// wings must straddle the body or they render entirely on top of it.
// Mirrors horizontally when walking left, since only the right-facing row
// of each sheet is ever loaded.
function drawCharacter(viewer, frameColumn, x, y) {
  const mirrored = viewer.direction < 0;

  ctx.save();
  if (mirrored) {
    ctx.translate(x + frameWidth, y);
    ctx.scale(-1, 1);
  } else {
    ctx.translate(x, y);
  }

  if (viewer.acessorio === manifest.wing_accessory) {
    drawSpriteLayer(loadImage(manifest.wings.bg), frameColumn, 0, 0);
  }

  ctx.drawImage(getTintedBase(frameColumn, viewer.cor), 0, 0);

  if (viewer.chapeu && manifest.hats[viewer.chapeu]) {
    drawSpriteLayer(loadImage(manifest.hats[viewer.chapeu]), frameColumn, 0, 0);
  }

  if (viewer.acessorio && viewer.acessorio !== manifest.wing_accessory && manifest.accessories[viewer.acessorio]) {
    drawSpriteLayer(loadImage(manifest.accessories[viewer.acessorio]), frameColumn, 0, 0);
  }

  if (viewer.acessorio === manifest.wing_accessory) {
    drawSpriteLayer(loadImage(manifest.wings.fg), frameColumn, 0, 0);
  }

  ctx.restore();
}

// --- Per-frame drawing ---

function drawBadges(viewer, yOffset) {
  let label = "";
  if (viewer.is_broadcaster) label = "♛";
  else if (viewer.is_mod) label = "MOD";
  if (label) {
    ctx.fillStyle = "#ffffff";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(label, viewer.x + frameWidth / 2, yOffset - 14);
  }
  if (viewer.is_sub) {
    ctx.strokeStyle = "#f6c90e";
    ctx.lineWidth = 1;
    ctx.strokeRect(viewer.x - 1, yOffset - 1, frameWidth + 2, frameHeight + 2);
  }
}

function drawViewer(viewer, timestamp) {
  const dancing = timestamp < viewer.danceUntil;
  const cheering = timestamp < viewer.cheerUntil;
  const bounce = dancing ? Math.abs(Math.sin(timestamp / 120)) * 6 : 0;
  const yOffset = viewer.y - bounce;

  if (cheering) {
    ctx.beginPath();
    ctx.strokeStyle = "#ffd700";
    ctx.lineWidth = 2;
    ctx.arc(viewer.x + frameWidth / 2, yOffset + frameHeight / 2, frameHeight * 0.7, 0, Math.PI * 2);
    ctx.stroke();
  }

  const frameColumn = walkFrameColumn(viewer.distanceWalked);
  drawCharacter(viewer, frameColumn, viewer.x, yOffset);

  drawBadges(viewer, yOffset);

  ctx.fillStyle = "#ffffff";
  ctx.font = "10px monospace";
  ctx.textAlign = "center";
  ctx.fillText(viewer.nick, viewer.x + frameWidth / 2, yOffset - 4);
}

let lastTimestamp = performance.now();

function tick(timestamp) {
  const deltaSeconds = (timestamp - lastTimestamp) / 1000;
  lastTimestamp = timestamp;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  if (assetsReady()) {
    for (const viewer of viewers.values()) {
      const travelled = viewer.speed * deltaSeconds;
      viewer.x += viewer.direction * travelled;
      viewer.distanceWalked += travelled;

      // Patrol back and forth instead of vanishing off one edge and
      // reappearing on the other. Re-roll speed on every bounce so it keeps
      // varying over time, not just once at spawn.
      if (viewer.x <= 0) {
        viewer.x = 0;
        viewer.direction = 1;
        viewer.speed = randomSpeed();
      } else if (viewer.x >= canvas.width - frameWidth) {
        viewer.x = canvas.width - frameWidth;
        viewer.direction = -1;
        viewer.speed = randomSpeed();
      }

      drawViewer(viewer, timestamp);
    }
  }

  requestAnimationFrame(tick);
}

resizeCanvas();
window.addEventListener("resize", resizeCanvas);

connect();
loadManifest();
requestAnimationFrame(tick);
```

- [ ] **Step 2: Write the throwaway Node.js verification harness**

Save this as `verify_sprites.js` in your working directory (NOT inside `web/` or any tracked path — delete it in Step 5, never commit it):

```javascript
const vm = require("vm");
const fs = require("fs");

const src = fs.readFileSync("web/overlay.js", "utf-8") + "\n" +
  "this.viewers = viewers; this.loadManifest = loadManifest; this.upsertViewer = upsertViewer; " +
  "this.getShadingMask = getShadingMask; this.getTintedBase = getTintedBase; " +
  "this.walkFrameColumn = walkFrameColumn; this.assetsReady = assetsReady; " +
  "this.drawCharacter = drawCharacter; this.tick = tick; this.imageCache = imageCache; " +
  "this.tintCache = tintCache; this.shadingMaskCache = shadingMaskCache;\n";

function makeFakeCanvasContext(log) {
  return {
    drawImage: (...args) => log.push(["drawImage", ...args.slice(-4)]),
    fillRect: (...args) => log.push(["fillRect", ...args]),
    clearRect: () => {},
    beginPath: () => {},
    arc: () => {},
    stroke: () => {},
    strokeRect: () => {},
    fillText: () => {},
    save: () => log.push(["save"]),
    restore: () => log.push(["restore"]),
    translate: (...args) => log.push(["translate", ...args]),
    scale: (...args) => log.push(["scale", ...args]),
    set fillStyle(v) { log.push(["fillStyle", v]); },
    set strokeStyle(v) {},
    set lineWidth(v) {},
    set font(v) {},
    set textAlign(v) {},
    set globalCompositeOperation(v) { log.push(["compositeOp", v]); },
    getImageData: (x, y, w, h) => ({ data: new Uint8ClampedArray(w * h * 4).fill(200) }),
    putImageData: () => {},
  };
}

function makeContext(width, height, fetchImpl) {
  const canvasLog = [];
  const mainCtx = makeFakeCanvasContext(canvasLog);
  const canvas = { width, height, getContext: () => mainCtx };

  const offscreenLogs = [];
  const context = {
    document: {
      getElementById: () => canvas,
      createElement: (tag) => {
        const log = [];
        offscreenLogs.push(log);
        return { width: 0, height: 0, getContext: () => makeFakeCanvasContext(log) };
      },
    },
    window: { innerWidth: width, innerHeight: height, addEventListener: () => {} },
    location: { protocol: "http:", host: "localhost" },
    WebSocket: class { constructor() {} },
    performance: { now: () => 0 },
    requestAnimationFrame: () => {},
    fetch: fetchImpl,
    Image: class {
      constructor() {
        this._src = "";
        this.complete = true;
        this.naturalWidth = 64;
      }
      set src(v) { this._src = v; }
      get src() { return this._src; }
    },
    console,
  };
  vm.createContext(context);
  vm.runInContext(src, context);
  return { context, canvasLog, offscreenLogs };
}

const fakeManifest = {
  frame_width: 64,
  frame_height: 64,
  sheet_columns: 9,
  sheet_rows: 4,
  direction_row: { up: 0, left: 1, down: 2, right: 3 },
  walk_frame_columns: [1, 2, 3, 4, 5, 6, 7, 8],
  base_layers: ["body_walk.png", "head_walk.png"],
  hats: { "boné": "hat_bone_walk.png", "coroa": "hat_coroa_walk.png", "chifres": "chifres_walk.png" },
  accessories: { "óculos": "oculos_walk.png", "capa": "capa_walk.png" },
  wing_accessory: "asas",
  wings: { bg: "asas_bg_walk.png", fg: "asas_fg_walk.png" },
};

async function fakeFetch() {
  return { json: async () => fakeManifest };
}

(async () => {
  // Test 1: walkFrameColumn cycles through the 8 walk columns by distance
  {
    const { context } = makeContext(500, 100, fakeFetch);
    await context.loadManifest();
    const seen = [];
    for (let d = 0; d < 8 * 8; d += 8) seen.push(context.walkFrameColumn(d));
    const ok = JSON.stringify(seen) === JSON.stringify([1, 2, 3, 4, 5, 6, 7, 8]);
    console.log("walkFrameColumn cycles 1..8:", ok ? "PASS" : "FAIL", seen);
  }

  // Test 2: getShadingMask is cached (same object on second call)
  {
    const { context } = makeContext(500, 100, fakeFetch);
    await context.loadManifest();
    const a = context.getShadingMask(1);
    const b = context.getShadingMask(1);
    console.log("getShadingMask caches per frame:", a === b ? "PASS" : "FAIL");
  }

  // Test 3: getTintedBase is cached per (frame, color), distinct across colors
  {
    const { context } = makeContext(500, 100, fakeFetch);
    await context.loadManifest();
    const red1 = context.getTintedBase(1, "#ff0000");
    const red2 = context.getTintedBase(1, "#ff0000");
    const blue = context.getTintedBase(1, "#0000ff");
    console.log("getTintedBase caches same (frame,color):", red1 === red2 ? "PASS" : "FAIL");
    console.log("getTintedBase differs across colors:", red1 !== blue ? "PASS" : "FAIL");
  }

  // Test 4: getTintedBase uses multiply then destination-in (transparency-safe tint)
  {
    const { context, offscreenLogs } = makeContext(500, 100, fakeFetch);
    await context.loadManifest();
    offscreenLogs.length = 0;
    context.getTintedBase(2, "#00ff00");
    const tintLog = offscreenLogs[offscreenLogs.length - 1];
    const ops = tintLog.filter((e) => e[0] === "compositeOp").map((e) => e[1]);
    const ok = ops.includes("multiply") && ops.includes("destination-in") &&
      ops.indexOf("multiply") < ops.indexOf("destination-in");
    console.log("tint uses multiply then destination-in:", ok ? "PASS" : "FAIL", ops);
  }

  // Test 5: drawCharacter layer order — wings bg, body, hat, accessory, wings fg
  {
    const { context, canvasLog } = makeContext(500, 100, fakeFetch);
    await context.loadManifest();
    canvasLog.length = 0;
    const viewer = { cor: "#ff8800", chapeu: "coroa", acessorio: "asas", direction: 1 };
    context.drawCharacter(viewer, 1, 10, 10);
    const draws = canvasLog.filter((e) => e[0] === "drawImage");
    // 4 drawImage calls expected: wings.bg, tinted body (offscreen canvas), hat, wings.fg
    console.log("drawCharacter draws 4 layers with wings:", draws.length === 4 ? "PASS" : "FAIL", draws.length);
  }

  // Test 6: drawCharacter mirrors when direction is -1
  {
    const { context, canvasLog } = makeContext(500, 100, fakeFetch);
    await context.loadManifest();
    canvasLog.length = 0;
    const viewer = { cor: "#123456", chapeu: null, acessorio: null, direction: -1 };
    context.drawCharacter(viewer, 1, 50, 20);
    const scaleCall = canvasLog.find((e) => e[0] === "scale");
    console.log("drawCharacter mirrors left-facing:", scaleCall && scaleCall[1] === -1 && scaleCall[2] === 1 ? "PASS" : "FAIL");
  }

  // Test 7: assetsReady is false before manifest loads, true after
  {
    const { context } = makeContext(500, 100, fakeFetch);
    console.log("assetsReady false before load:", context.assetsReady() === false ? "PASS" : "FAIL");
    await context.loadManifest();
    console.log("assetsReady true after load:", context.assetsReady() === true ? "PASS" : "FAIL");
  }

  // Test 8: upsertViewer preserves direction/speed/distanceWalked across re-broadcast
  {
    const { context } = makeContext(500, 100, fakeFetch);
    await context.loadManifest();
    context.upsertViewer({ username: "gina", nick: "g", cor: "#111111", chapeu: null, acessorio: null, dance_remaining: 0, cheer_remaining: 0 });
    const first = context.viewers.get("gina");
    first.distanceWalked = 42;
    context.upsertViewer({ username: "gina", nick: "g", cor: "#222222", chapeu: null, acessorio: null, dance_remaining: 0, cheer_remaining: 0 });
    const second = context.viewers.get("gina");
    const ok = second.direction === first.direction && second.speed === first.speed && second.distanceWalked === 42 && second.cor === "#222222";
    console.log("upsertViewer preserves motion state, updates cor:", ok ? "PASS" : "FAIL");
  }
})();
```

- [ ] **Step 3: Run the harness, fix anything that FAILs**

Run: `node verify_sprites.js`
Expected: all 8 checks print `PASS`. If any print `FAIL`, the bug is in `web/overlay.js` (the harness mirrors the spec's documented behavior exactly) — fix the code, not the test, unless you find the harness itself asserts something the spec doesn't actually require.

- [ ] **Step 4: Manual visual sanity check**

This cannot be automated — do it yourself:

1. From `D:\git-projeto\chat-parade`, run `python -m chat_parade.main` (or `run.bat`).
2. Open `http://localhost:8901/overlay` in a normal browser tab. Open the browser's dev tools console and confirm `GET /static/assets/lpc/manifest.json` and the PNG requests return 200, not 404 — that confirms the mount path used in Step 1 is correct against the real server (the harness only stubs `fetch`/`Image`, it can't catch a wrong URL).
3. Seeing a walking character also requires a viewer to actually be present, which needs either a live Twitch chat message or a quick manual push — this part needs a live setup to fully confirm visually. If you have one, type `!cor blue`, `!chapeu coroa`, `!acessorio asas` in chat and confirm: a real LPC character (not a blob) walks across, wearing a gold crown and wings rendering both behind and in front of the body, tinted blue with visible shading (not a flat color fill).

- [ ] **Step 5: Delete the throwaway harness and run the Python suite**

```bash
rm verify_sprites.js
```

Run: `pytest -v`
Expected: PASS — Task 2 touched no Python file, this just confirms nothing else broke.

- [ ] **Step 6: Commit**

```bash
git add web/overlay.js
git commit -m "Render real LPC sprites with walk-cycle animation and runtime recolor"
```

---

### Task 3: README credits and cleanup

**Files:**
- Modify: `README.md`

**Interfaces:** none — documentation only.

- [ ] **Step 1: Add a Créditos section**

Add this new section to `README.md`, right before the `## Testes` section at the end:

```markdown
## Créditos

Os avatares usam sprites do [Liberated Pixel Cup](https://lpc.opengameart.org)
(CC-BY-SA 3.0 / GPL 3.0), gerados via o
[Universal LPC Spritesheet Character Generator](https://liberatedpixelcup.github.io/Universal-LPC-Spritesheet-Character-Generator/).

- `body/bodies/male/walk.png` — 'Thick' Male Revised Run/Climb by JaidynReiman
  (based on ElizaWy's LPC Revised). Autores: bluecarrot16, JaidynReiman,
  Benjamin K. Smith (BenCreating), Evert, Eliza Wyatt (ElizaWy), TheraHedwig,
  MuffinElZangano, Durrani, Johannes Sjölund (wulax), Stephen Challener (Redshrike).
- `head/heads/human/male/walk.png` — original head by Redshrike, tweaks by
  BenCreating, modular version by bluecarrot16. Autores: bluecarrot16,
  Benjamin K. Smith (BenCreating), Stephen Challener (Redshrike).
- `hat/cloth/leather_cap/adult/walk/walnut.png` — original by Johannes
  Sjölund (wulax), female by Matthew Krohn, mapped to all frames w/recolors
  by JaidynReiman. Autores: Johannes Sjölund (wulax), Matthew Krohn (Makrohn),
  JaidynReiman.
- `hat/formal/crown/adult/walk/crown_gold.png` — Autores: DarkwallLKE,
  Charles Sanchez (CharlesGabriel).
- `head/horns/curled/adult/walk.png` — Curled Horns. Créditos exatos a
  confirmar: gere a combinação final no gerador (corpo + leather cap walnut +
  crown gold + curled horns + glasses black + iverness cloak black +
  feathered wings ash) e clique "Credits (TXT)" pra pegar a atribuição
  completa e correta desse item especificamente.
- `facial/glasses/glasses/adult/walk/black.png` — Autor: ElizaWy.
- `torso/jacket/iverness/male/walk/black.png` — Autor: bluecarrot16.
- `body/wings/feathered/adult/{bg,fg}/walk/ash.png` — original by ElizaWy,
  added to most remaining frames by JaidynReiman. Autores: ElizaWy,
  Stephen Challener (Redshrike), JaidynReiman.
```

- [ ] **Step 2: Fix the stale "geração de avatar" reference in Testes**

In the `## Testes` section, replace:

```markdown
`pytest` roda toda a suíte (parsing de comando, geração de avatar, estado
persistido, servidor web).
```

with:

```markdown
`pytest` roda toda a suíte (parsing de comando, estado persistido, servidor
web). A renderização do sprite (fatiamento de frame, composição de camadas,
recolor) não tem suíte automatizada — ver `docs/superpowers/plans/2026-08-30-lpc-pixelart-avatars.md`
pra como verificar isso manualmente.
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "Add LPC asset credits to README, fix stale avatar-generation test mention"
```
