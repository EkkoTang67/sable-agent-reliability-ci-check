import { getPublicCheckoutConfig } from "../../lib/paypal_checkout.mjs";
import { applyPublicCors, sendMethodNotAllowed } from "../../lib/http.mjs";

export default function handler(req, res) {
  if (!applyPublicCors(req, res, ["GET"])) return;
  if (req.method !== "GET") return sendMethodNotAllowed(res, ["GET"]);
  res.setHeader("Cache-Control", "no-store, max-age=0");
  return res.status(200).json(getPublicCheckoutConfig());
}
