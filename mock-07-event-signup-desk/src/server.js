const mongoose = require("mongoose");
const app = require("./app");

const PORT = process.env.PORT || 3000;
const MONGODB_URI = process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/event-signup-desk";

mongoose.connect(MONGODB_URI).then(() => {
  app.listen(PORT, () => console.log(`Event sign-up desk listening on ${PORT}`));
});
