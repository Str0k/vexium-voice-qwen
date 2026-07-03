// Shared bridge-URL resolvers (WS voice path + HTTP api path).
//  - explicit env override wins (deploys where the bridge lives elsewhere);
//  - on localhost, talk to the local bridge on :8000;
//  - otherwise SAME origin (the tunnel / reverse proxy serves both).

export function resolveBridgeUrl(vertical) {
  const q = vertical && vertical !== "dental" ? `?v=${encodeURIComponent(vertical)}` : "";
  if (process.env.NEXT_PUBLIC_BRIDGE_URL) return process.env.NEXT_PUBLIC_BRIDGE_URL + q;
  if (typeof window !== "undefined") {
    const { protocol, hostname, host } = window.location;
    if (hostname === "localhost" || hostname === "127.0.0.1") return "ws://localhost:8000/ws" + q;
    return `${protocol === "https:" ? "wss" : "ws"}://${host}/ws` + q;
  }
  return "ws://localhost:8000/ws" + q;
}

export function resolveHttpBase() {
  if (process.env.NEXT_PUBLIC_BRIDGE_HTTP) return process.env.NEXT_PUBLIC_BRIDGE_HTTP;
  if (typeof window !== "undefined") {
    const { protocol, hostname, origin } = window.location;
    if (hostname === "localhost" || hostname === "127.0.0.1") return "http://localhost:8000";
    return origin;
  }
  return "http://localhost:8000";
}
