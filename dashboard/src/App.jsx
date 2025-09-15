import React, { useEffect, useState } from "react";
import WsClient from "./ws-client";
import LiveSignals from "./components/LiveSignals";
import TradeMonitor from "./components/TradeMonitor";
import StrategyControls from "./components/StrategyControls";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";

/**
 * High level App. Creates a single WS client and passes it down.
 */
export default function App() {
  const [client] = useState(() => new WsClient(WS_URL, { heartbeatInterval: 20_000 }));
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState({});

  useEffect(() => {
    function onOpen() {
      setConnected(true);
    }
    function onClose() {
      setConnected(false);
    }
    function onStatus(payload) {
      setStatus(payload);
    }

    client.on("open", onOpen);
    client.on("close", onClose);
    client.on("strategy_status", onStatus);

    // initialize connection
    client.connect();

    return () => {
      client.off("open", onOpen);
      client.off("close", onClose);
      client.off("strategy_status", onStatus);
      client.disconnect();
    };
  }, [client]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <h1>Forex Power Scalper — Dashboard</h1>
        <div className="connection">
          <span className={`dot ${connected ? "online" : "offline"}`}></span>
          <span>{connected ? "Connected" : "Offline"}</span>
        </div>
      </header>

      <main className="container">
        <section className="left-col">
          <LiveSignals ws={client} />
          <StrategyControls ws={client} status={status} />
        </section>

        <section className="right-col">
          <TradeMonitor ws={client} />
        </section>
      </main>

      <footer className="footer">
        <small>Connected to: {WS_URL}</small>
      </footer>
    </div>
  );
}
