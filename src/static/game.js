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

class Game {
  constructor(competition_id) {
    this.map = [];
    this.competition_id = competition_id;
    this.last_log_id = 0;
    this.logs_applied = {};

    const gameView = document.getElementById("game-view");

    for (let offset = 0; offset < 128 * 128; offset++) {
      const tile = createTile("-");
      tile.onclick = async (ev) => {
        const x = offset % 128;
        const y = Math.floor(offset / 128);
        const res = await req("/api/open_tile", {
          competition_id: this.competition_id,
          x,
          y,
        });
        await this.ApplyLog(res.log_id);
      };
      tile.oncontextmenu = (ev) => {
        (async () => {
          const x = offset % 128;
          const y = Math.floor(offset / 128);
          const res = await req("/api/toggle_tile", {
            competition_id: this.competition_id,
            x,
            y,
          });
          await this.ApplyLog(res.log_id);
        })().catch(console.log);
        return false;
      };
      this.map.push(tile);
      gameView.appendChild(tile);
    }
  }

  SetC(cx, cy, x, y, v) {
    const rx = cx * 16 + x;
    const ry = cy * 16 + y;
    const offset = rx + ry * 128;
    this.map[offset].className = `tile t-${v}`;
  }

  async ApplyLog(id) {
    const log = await req("/api/get_log", { log_id: id });
    if (log.competition_id !== this.competition_id) {
      console.log(log, this.competition_id);
      throw "not the same competition wtf";
    }
    const action = JSON.parse(log.action);
    for (const mc of JSON.parse(action.modified_chunks)) {
      // get chunk
      const chunk = await req("/api/get_chunk", {
        competition_id: this.competition_id,
        x: mc[0],
        y: mc[1],
      });
      await this.RenderChunk(chunk);
    }
    this.logs_applied[id] = true;
  }

  async RenderChunk(chunk) {
    const data = chunk.cdata;
    const cx = chunk.x;
    const cy = chunk.y;
    for (let k = 0; k < data.length; k++) {
      const x = k % 16;
      const y = Math.floor(k / 16);
      this.SetC(cx, cy, x, y, data[k]);
    }
  }

  async InitMap() {
    const chunks = await req("/api/get_field", {
      competition_id: this.competition_id,
    });

    for (const chunk of chunks) {
      await this.RenderChunk(chunk);
    }

    const past_logs = await req("/api/get_past_logs_ids", {
      competition_id: this.competition_id,
    });
    for (const pl of past_logs) {
      this.logs_applied[pl.id] = true;
      this.last_log_id = Math.max(this.last_log_id, pl.id);
    }

    const ab = document.querySelector("#activate");
    ab.onclick = async () => {
      try {
        const res = await req("/api/activate", {
          competition_id: this.competition_id,
        });
        await this.ApplyLog(res.log_id);
      } catch (ex) {
        alert("On Cooldown");
      }
    };

    window.poll_interval = setInterval(() => {
      this.Poll();
    }, 200);
  }

  async Poll() {
    const logs = await req("/api/get_logs_after", {
      competition_id: this.competition_id,
      log_id: this.last_log_id,
    });
    for (const log of logs) {
      if (!this.logs_applied[log.id]) {
        await this.ApplyLog(log.id);
      }
      this.last_log_id = Math.max(this.last_log_id, log.id);
    }

    const lb_data = await req("/api/leaderboard", {
      competition_id: this.competition_id,
    });
    lb_data.sort((a, b) => b.score - a.score);
    const tb = document.querySelector("#leaderboard_table");
    tb.innerHTML = "";
    for (const lb of lb_data) {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${lb.u.username}</td> <td>${lb.score}</td> <td>${lb.mines_hit}</td>`;
      tb.appendChild(tr);
    }

    //console.log(logs);
  }
}

async function Main() {
  console.log(await req("/api/me", {}));
  console.log(window.competition_id);
  window.competition_id = parseInt(window.competition_id);
  const game = new Game(window.competition_id);
  await game.InitMap();
}

Main().catch(console.log);

function stop() {
  clearInterval(window.poll_interval);
}
