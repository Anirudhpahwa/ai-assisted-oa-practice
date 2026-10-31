/** Identifies the acting user from the X-User-Id header. */
function actor(req, res, next) {
  const userId = (req.get("X-User-Id") || "").trim();
  if (!userId) {
    return res.status(401).json({ error: "X-User-Id header required" });
  }
  req.userId = userId;
  next();
}

module.exports = { actor };
