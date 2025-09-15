
 */
import { WebSocketServer } from "ws";

const wss = new WebSocketServer({ port: 8000 });
console.log("Mock WS server listening ws://localhost:8000/ws");

function broadcast(ws, type, payload = {}) {
  const message = JSON.stringify({ type, payload });
  ws.send(message);
}

function randomSignal() {
  const pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"];
  const side = Math.random() > 0.5 ? "BUY" : "SELL";
  return {
    id: Math.floor(Math.random() * 1e8),
    pair: pairs[Math.floor(Math.random() * pairs.length)],
    side,
    price: (1 + Math.random() * 0.02).toFixed(5),
    confidence: (Math.random()).toFixed(2),
    ts: Date.now()
  };
}

function randomTrade() {
  return {
    id: Math.floor(Math.random() * 1e8),
    pair: "EURUSD",
    side: Math.random() > 0.5 ? "LONG" : "SHORT",
    entry: (1 + Math.random() * 0.02).toFixed(5),
    size: (Math.random() * 0.5).toFixed(3),
    pnl: (Math.random()*2 - 1).toFixed(3),
    ts: Date.now()
  };
}

wss.on("connection", (ws, req) => {
  console.log("client connected");
  ws.on("message", (msg) => {
    try {
      const data = JSON.parse(msg.toString());
      if (data.type === "ping") {
        ws.send(JSON.stringify({ type: "ack", request_id: data.request_id || null, payload: { pong: Date.now() } }));
      } else if (data.type === "command") {
        ws.send(JSON.stringify({ type: "ack", request_id: data.request_id || null, payload: { ok: true, cmd: data.payload } }));
      }
    } catch (e) {
      // ignore
    }
  });

  const iv1 = setInterval(() => {
    broadcast(ws, "signal", randomSignal());
  }, 2500);

  const iv2 = setInterval(() => {
    broadcast(ws, "trade", randomTrade());
  }, 4100);

  const iv3 = setInterval(() => {
    broadcast(ws, "strategy_status", { enabled: Math.random() > 0.2, version: "v1.2.3", ts: Date.now() });
  }, 7000);

  ws.on("close", () => {
    clearInterval(iv1);
    clearInterval(iv2);
    clearInterval(iv3);
    console.log("client disconnected");
  });
});
