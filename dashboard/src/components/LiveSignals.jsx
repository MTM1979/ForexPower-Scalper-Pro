import React, { useEffect, useState } from "react";
import { format } from "date-fns";


 */
export default function LiveSignals({ ws }) {
  const [signals, setSignals] = useState([]);

  useEffect(() => {
    function onSignal(payload) {
      setSignals(prev => {
        const next = [payload, ...prev].slice(0, 30);
        return next;
      });
    }
    ws.on("signal", onSignal);
    return () => ws.off("signal", onSignal);
  }, [ws]);

  return (
    <div className="card">
      <div className="card-header">
        <h3>Live Signals</h3>
        <small className="muted">Latest market signals from strategy</small>
      </div>

      <div className="card-body">
        {signals.length === 0 ? (
          <div className="empty">No signals yet</div>
        ) : (
          <table className="signals-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Pair</th>
                <th>Side</th>
                <th>Price</th>
                <th>Conf</th>
              </tr>
            </thead>
            <tbody>
              {signals.map(sig => (
                <tr key={sig.id}>
                  <td>{format(new Date(sig.ts), "HH:mm:ss")}</td>
                  <td>{sig.pair}</td>
                  <td className={sig.side?.toLowerCase() === "buy" ? "buy" : "sell"}>{sig.side}</td>
                  <td>{sig.price}</td>
                  <td>{Number(sig.confidence).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
