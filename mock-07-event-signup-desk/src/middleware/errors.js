const { HttpError } = require("../errors");

function notFound(req, res) {
  res.status(404).json({ error: "route not found" });
}

// eslint-disable-next-line no-unused-vars
function handleErrors(err, req, res, next) {
  if (err instanceof HttpError) {
    return res.status(err.status).json({ error: err.message });
  }
  if (err.type === "entity.parse.failed") {
    return res.status(400).json({ error: "invalid JSON body" });
  }
  console.error(err);
  res.status(500).json({ error: "internal error" });
}

module.exports = { notFound, handleErrors };
