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
