const express = require("express");
const { actor } = require("./middleware/actor");
const { notFound, handleErrors } = require("./middleware/errors");
const eventRoutes = require("./routes/events");

const app = express();

app.use(express.json());
app.use("/api", actor);
app.use("/api/events", eventRoutes);
app.use(notFound);
app.use(handleErrors);

module.exports = app;
