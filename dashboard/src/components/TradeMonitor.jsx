import React, { useEffect, useState } from "react";


 */
export default function TradeMonitor({ ws }) {
  const [trades, setTrades] = useState([]);
  const [positions, setPositions] = useState([]);

  useEffect(() => {
    function onTrade(payload) {
      setTrades(prev => [payload, ...prev].slice(0, 100));
    }
    function onPosition(payload) {
      // payload expected to be an array or single position
      if (Array.isArray(payload)) {
        setPositions(payload);
      } else {
        setPositions(prev => {
          const idx = prev.findIndex(p => p.id === payload.id);
          if (idx === -1) return [payload, ...prev].slice(0, 50);
          const copy = [...prev];
          copy[idx] = payload;
          return copy;
        });
      }
    }

    ws.on("trade", onTrade);
    ws.on("position", onPosition);

    return () => {
      ws.off("trade", onTrade);
      ws.off("position", onPosition);
    };
  }, [ws]);

  const totalPnL = trades.reduce((acc, t) => acc + (parseFloat(t.pnl) || 0), 0);

  return (
    <div className="card">
      <div className="card-header">
        <h3>Trade Monitor</h3>
        <small className="muted">Recent trades · Open positions</small>
      </div>

      <div className="card-body">
        <div className="summary-row">
          <div>
            <strong>Recent PnL</strong>
            <div className={`pnl ${totalPnL >= 0 ? "positive" : "negative"}`}>{totalPnL.toFixed(3)}</div>
          </div>
          <div>
            <strong>Open positions</strong>
            <div>{positions.length}</div>
          </div>
        </div>

        <h4>Open Positions</h4>
        {positions.length === 0 ? <div className="empty">No open positions</div> : (
          <ul className="positions">
            {positions.map(p => (
              <li key={p.id} className="position">
                <div className="pos-left">
                  <div className="pair">{p.pair}</div>
                  <div className="side">{p.side}</div>
                </div>
                <div className="pos-right">
                  <div>Entry: {p.entry}</div>
                  <div>Size: {p.size}</div>
                  <div>PnL: <span className={p.pnl >= 0 ? "positive" : "negative"}>{Number(p.pnl).toFixed(3)}</span></div>
                </div>
              </li>
            ))}
          </ul>
        )}

        <h4>Recent Trades</h4>
        <table className="trades-table">
          <thead>
            <tr><th>Pair</th><th>Type</th><th>Entry</th><th>Size</th><th>PnL</th></tr>
          </thead>
          <tbody>
            {trades.map(t => (
              <tr key={t.id}>
                <td>{t.pair}</td>
                <td>{t.side}</td>
                <td>{t.entry}</td>
                <td>{t.size}</td>
                <td className={t.pnl >= 0 ? "positive" : "negative"}>{Number(t.pnl).toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
