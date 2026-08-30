const PIXEL_SIZE = 4;
const SPEED_PX_PER_SEC = 60;
const canvas = document.getElementById("parade");
const ctx = canvas.getContext("2d");

const viewers = new Map();

function laneY() {
  return canvas.height - PIXEL_SIZE * 13 - 10;
}

// The OBS Browser Source can be any size the streamer picks, so track the
// window instead of assuming a hardcoded 1920x160. laneY() and spawnX() both
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

function spawnX() {
  return canvas.width + Math.random() * 200;
}

function upsertViewer(payload) {
  const existing = viewers.get(payload.username);
  const x = existing ? existing.x : spawnX();
  // The server sends seconds remaining, not booleans: turn them into absolute
  // deadlines on the same clock tick() uses so drawViewer can re-check them
  // every frame instead of latching a stale boolean until the next broadcast.
  const now = performance.now();
  viewers.set(payload.username, {
    ...payload,
    x,
    y: laneY(),
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

function drawBadges(viewer, yOffset, width) {
  let label = "";
  if (viewer.is_broadcaster) label = "♛";
  else if (viewer.is_mod) label = "MOD";
  if (label) {
    ctx.fillStyle = "#ffffff";
    ctx.font = "10px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(label, viewer.x + width / 2, yOffset - 14);
  }
  if (viewer.is_sub) {
    ctx.strokeStyle = "#f6c90e";
    ctx.lineWidth = 1;
    ctx.strokeRect(viewer.x - 1, yOffset - 1, width + 2, viewer.grid.length * PIXEL_SIZE + 2);
  }
}

function drawViewer(viewer, timestamp) {
  const grid = viewer.grid;
  const width = grid[0].length * PIXEL_SIZE;
  const dancing = timestamp < viewer.danceUntil;
  const cheering = timestamp < viewer.cheerUntil;
  const bounce = dancing ? Math.abs(Math.sin(timestamp / 120)) * 6 : 0;
  const yOffset = viewer.y - bounce;

  if (cheering) {
    ctx.beginPath();
    ctx.strokeStyle = "#ffd700";
    ctx.lineWidth = 2;
    ctx.arc(
      viewer.x + width / 2,
      yOffset + (grid.length * PIXEL_SIZE) / 2,
      grid.length * PIXEL_SIZE * 0.7,
      0,
      Math.PI * 2
    );
    ctx.stroke();
  }

  for (let row = 0; row < grid.length; row++) {
    for (let col = 0; col < grid[row].length; col++) {
      const color = grid[row][col];
      if (!color) continue;
      ctx.fillStyle = color;
      ctx.fillRect(viewer.x + col * PIXEL_SIZE, yOffset + row * PIXEL_SIZE, PIXEL_SIZE, PIXEL_SIZE);
    }
  }

  drawBadges(viewer, yOffset, width);

  ctx.fillStyle = "#ffffff";
  ctx.font = "10px monospace";
  ctx.textAlign = "center";
  ctx.fillText(viewer.nick, viewer.x + width / 2, yOffset - 4);
}

let lastTimestamp = performance.now();

function tick(timestamp) {
  const deltaSeconds = (timestamp - lastTimestamp) / 1000;
  lastTimestamp = timestamp;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  for (const viewer of viewers.values()) {
    viewer.x -= SPEED_PX_PER_SEC * deltaSeconds;
    const width = viewer.grid[0].length * PIXEL_SIZE;
    if (viewer.x < -width) {
      viewer.x = spawnX();
    }
    drawViewer(viewer, timestamp);
  }

  requestAnimationFrame(tick);
}

resizeCanvas();
window.addEventListener("resize", resizeCanvas);

connect();
requestAnimationFrame(tick);
