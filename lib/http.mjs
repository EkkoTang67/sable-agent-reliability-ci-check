export function applyPublicCors(req, res, methods = ["GET", "POST"]) {
  const raw = String(process.env.SABLE_ALLOWED_ORIGINS || "").trim();
  const deploymentHost = String(process.env.VERCEL_URL || "").trim().replace("https://", "").replace("http://", "").split("/")[0];
  const deploymentOrigin = deploymentHost ? `https://${deploymentHost}` : "";
  const allowed = raw
    ? raw.split(",").map((x) => x.trim()).filter(Boolean)
    : [
      "https://socksninja.github.io",
      "https://sable-cash.vercel.app",
      "https://sable-cash-1164752614-9151.vercel.app",
      "https://sable-code-to-cash.vercel.app",
      "https://sable-code-to-cash-sandbox.vercel.app",
    ];
  const origin = String(req.headers?.origin || "").trim();
  res.setHeader("Vary", "Origin");
  res.setHeader("Access-Control-Allow-Methods", [...methods, "OPTIONS"].join(", "));
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Access-Control-Max-Age", "600");
  if (origin && !allowed.includes(origin) && origin !== deploymentOrigin) {
    res.status(403).json({ error: "origin_not_allowed" });
    return false;
  }
  if (origin) res.setHeader("Access-Control-Allow-Origin", origin);
  else res.setHeader("Access-Control-Allow-Origin", "*");

  if (req.method === "OPTIONS") {
    res.status(204).end();
    return false;
  }
  return true;
}

export function sendMethodNotAllowed(res, methods) {
  res.setHeader("Allow", methods.join(", "));
  return res.status(405).json({ error: "method_not_allowed" });
}

export function safeErrorStatus(error) {
  const status = Number(error?.status);
  if ([400, 401, 403, 404, 409, 422, 429].includes(status)) return status;
  return 502;
}
