import React, { useEffect, useState } from "react";


 */
export default function StrategyControls({ ws, status: initialStatus = {} }) {
  const [status, setStatus] = useState(initialStatus);
  const [sending, setSending] = useState(false);
  const [params, setParams] = useState({
    risk_per_trade: initialStatus.risk_per_trade || 0.01,
    enabled: !!initialStatus.enabled
  });

  useEffect(() => {
    function onStatus(payload) {
      setStatus(payload);
      setParams(prev => ({ ...prev, enabled: !!payload.enabled }));
    }
    ws.on("strategy_status", onStatus);
    return () => ws.off("strategy_status", onStatus);
  }, [ws]);

  async function toggleEnabled() {
    const newEnabled = !params.enabled;
    setParams(p => ({ ...p, enabled: newEnabled }));
    setSending(true);
    try {
      await ws.send({ type: "command", payload: { action: "set_enabled", enabled: newEnabled } }, { awaitAck: true, timeout: 3000 });
      // optimistic already applied; server will send strategy_status eventually
    } catch (e) {
      console.error(e);
      // revert on error
      setParams(p => ({ ...p, enabled: !newEnabled }));
      alert("Failed to change enabled state: " + e.message);
    } finally {
      setSending(false);
    }
  }

  async function updateParam(key, value) {
    setParams(p => ({ ...p, [key]: value }));
    setSending(true);
    try {
      await ws.send({ type: "command", payload: { action: "update_param", param: key, value } }, { awaitAck: true });
    } catch (e) {
      console.error(e);
      alert("Failed to update param: " + e.message);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3>Strategy Controls</h3>
        <small className="muted">Enable/disable and tune strategy</small>
      </div>

      <div className="card-body">
        <div className="status-row">
          <div>Version: <strong>{status.version || "—"}</strong></div>
          <div>Running: <strong>{String(status.enabled)}</strong></div>
        </div>

        <div className="controls">
          <div className="control-row">
            <label>Enabled</label>
            <button className={`btn ${params.enabled ? "btn-danger" : "btn-primary"}`} onClick={toggleEnabled} disabled={sending}>
              {params.enabled ? "Disable" : "Enable"}
            </button>
          </div>

          <div className="control-row">
            <label>Risk per trade</label>
            <input
              type="number"
              step="0.001"
              min="0"
              max="1"
              value={params.risk_per_trade}
              onChange={(e) => setParams(p => ({ ...p, risk_per_trade: parseFloat(e.target.value) }))}
            />
            <button className="btn" onClick={() => updateParam("risk_per_trade", params.risk_per_trade)} disabled={sending}>
              Update
            </button>
          </div>
        </div>

        <div className="muted" style={{ marginTop: 12 }}>
          Last reported: {status.ts ? new Date(status.ts).toLocaleString() : "—"}
        </div>
      </div>
    </div>
  );
}
