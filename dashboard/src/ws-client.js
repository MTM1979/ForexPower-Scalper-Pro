/**
 * Simple robust WebSocket client with:
 * - reconnect with exponential backoff
 * - subscribe/unsubscribe event handlers by event type
 * - send JSON commands with optional request id and awaits ack via 'ack' event
 *
 * Event message format (incoming):
 * {
 *   "type": "signal" | "trade" | "position" | "strategy_status" | "ack" | "error",
 *   "payload": { ... },
 *   "request_id": "optional"
 * }
 *
 * Outgoing commands should be objects; they will be JSON.stringify'ed.
 */
class WsClient {
  constructor(url, opts = {}) {
    this.url = url;
    this.ws = null;
    this._listeners = new Map(); // eventType -> Set(callback)
    this._anyListeners = new Set();
    this._nextRequestId = 1;
    this._pendingAcks = new Map();
    this._reconnectDelay = opts.reconnectDelay || 1000;
    this._maxReconnectDelay = opts.maxReconnectDelay || 30_000;
    this._backoffFactor = opts.backoffFactor || 1.6;
    this._heartbeatInterval = opts.heartbeatInterval || 20_000;
    this._heartbeatTimer = null;
    this._shouldReconnect = true;
  }

  connect() {
    if (this.ws) return;
    this._shouldReconnect = true;
    this._connectOnce();
  }

  _connectOnce() {
    this.ws = new WebSocket(this.url);

    this.ws.addEventListener("open", () => {
      this._reconnectDelay = 1000; // reset
      this._emit("open");
      this._startHeartbeat();
    });

    this.ws.addEventListener("close", (ev) => {
      this._emit("close", ev);
      this._stopHeartbeat();
      this.ws = null;
      if (this._shouldReconnect) {
        setTimeout(() => this._connectOnce(), this._reconnectDelay);
        this._reconnectDelay = Math.min(this._reconnectDelay * this._backoffFactor, this._maxReconnectDelay);
      }
    });

    this.ws.addEventListener("error", (err) => {
      this._emit("error", err);
    });

    this.ws.addEventListener("message", (msg) => {
      try {
        const data = JSON.parse(msg.data);
        const { type, payload, request_id } = data;
        if (type === "ack" && request_id) {
          const resolver = this._pendingAcks.get(request_id);
          if (resolver) {
            resolver.resolve(payload);
            this._pendingAcks.delete(request_id);
            return;
          }
        }
        this._emit(type, payload, data);
        this._emit("*", data);
      } catch (e) {
        this._emit("error", e);
      }
    });
  }

  disconnect() {
    this._shouldReconnect = false;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this._stopHeartbeat();
  }

  send(obj, { awaitAck = false, timeout = 5000 } = {}) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return Promise.reject(new Error("WebSocket is not open"));
    }
    const request_id = String(this._nextRequestId++);
    const packet = { ...obj, request_id };
    const json = JSON.stringify(packet);
    this.ws.send(json);
    if (!awaitAck) return Promise.resolve();

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this._pendingAcks.delete(request_id);
        reject(new Error("Ack timeout"));
      }, timeout);
      this._pendingAcks.set(request_id, {
        resolve: (payload) => {
          clearTimeout(timer);
          resolve(payload);
        }
      });
    });
  }

  on(eventType, cb) {
    if (eventType === "*") {
      this._anyListeners.add(cb);
      return;
    }
    if (!this._listeners.has(eventType)) {
      this._listeners.set(eventType, new Set());
    }
    this._listeners.get(eventType).add(cb);
  }

  off(eventType, cb) {
    if (eventType === "*") {
      this._anyListeners.delete(cb);
      return;
    }
    const s = this._listeners.get(eventType);
    if (s) s.delete(cb);
  }

  _emit(eventType, payload, full) {
    const s = this._listeners.get(eventType);
    if (s) {
      for (const cb of Array.from(s)) {
        try {
          cb(payload, full);
        } catch (e) {
          // swallow
          console.error("listener error", e);
        }
      }
    }
    for (const cb of Array.from(this._anyListeners)) {
      try {
        cb(eventType, payload, full);
      } catch (e) {
        console.error("any-listener error", e);
      }
    }
  }

  _startHeartbeat() {
    this._stopHeartbeat();
    this._heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        try {
          this.ws.send(JSON.stringify({ type: "ping", ts: Date.now() }));
        } catch (e) {
          // ignore
        }
      }
    }, this._heartbeatInterval);
  }

  _stopHeartbeat() {
    if (this._heartbeatTimer) {
      clearInterval(this._heartbeatTimer);
      this._heartbeatTimer = null;
    }
  }
}

export default WsClient;
