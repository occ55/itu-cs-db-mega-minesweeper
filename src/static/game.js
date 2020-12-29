function createTile(c) {
  const el = document.createElement("div");
  el.classList.add("tile");
  el.classList.add(`t-${c}`);
  return el;
}

function get(map, x, y) {
  const cx = Math.floor(x / 16);
  const cy = Math.floor(y / 16);
  const offset = (y % 16) * 16 + (x % 16);
  return map[cy][cx][offset];
}

async function Main() {
  console.log(await req("/api/me", {}));
  console.log(await req("/api/debug_tile", { competition_id: 10, x: 0, y: 0 }));
  const chunks = await req("/api/get_field", { competition_id: 10 });
  const full_map = [];
  for (const c of chunks) {
    if (!full_map[c.y]) {
      full_map[c.y] = [];
    }
    full_map[c.y][c.x] = c.cdata;
  }
  const gameView = document.getElementById("game-view");

  for (let y = 0; y < 128; y++) {
    for (let x = 0; x < 128; x++) {
      const tile = createTile(get(full_map, x, y));
      tile.onclick = async (ev) => {
        const res = await req("/api/debug_tile", { competition_id: 10, x, y });
        ev.target.className = `tile t-${res.data}`;
      };
      gameView.appendChild(tile);
    }
  }
}

Main().catch(console.log);
