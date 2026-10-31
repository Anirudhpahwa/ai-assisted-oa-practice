class HttpError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

/** Lets async route handlers reject into the Express error middleware. */
function wrap(handler) {
  return (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);
}

function isObjectId(value) {
  return typeof value === "string" && /^[0-9a-f]{24}$/i.test(value);
}

module.exports = { HttpError, wrap, isObjectId };
