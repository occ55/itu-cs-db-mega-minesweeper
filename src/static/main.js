async function createTile() {
  const el = document.createElement("div");
  el.classList.add("tile");
  return el;
}

async function Main() {
  const gameView = document.getElementById("game-view");

  for (let k = 0; k < 10000; k++) {
    //gameView.appendChild(await createTile());
  }
}

Main().catch(console.log);
