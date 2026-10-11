function originFromHost(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  try {
    return new URL(raw.includes("://") ? raw : `https://${raw}`).origin;
  } catch {
    return "";
  }
}

export function applyPublicCors(req, res, methods = ["GET", "POST"]) {
  const raw = String(process.env.SABLE_ALLOWED_ORIGINS || "").trim();
  // VERCEL_URL is the immutable deployment hostname; VERCEL_BRANCH_URL may be
  // the stable branch alias users actually visit. Both must be allowed because
  // the page calls these API routes with its own origin.
  const deploymentOrigins = new Set([
    originFromHost(process.env.VERCEL_URL),
    originFromHost(process.env.VERCEL_BRANCH_URL),
  ].filter(Boolean));
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
  if (origin && !allowed.includes(origin) && !deploymentOrigins.has(origin)) {
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
