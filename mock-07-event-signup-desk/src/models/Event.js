const mongoose = require("mongoose");

const eventSchema = new mongoose.Schema(
  {
    title: { type: String, required: true },
    location: { type: String, default: "" },
    startsAt: { type: Date, required: true },
    capacity: { type: Number, required: true },
    status: { type: String, enum: ["draft", "published", "cancelled"], default: "draft" },
    organizer: { type: String, required: true },
  },
  { timestamps: true }
);

module.exports = mongoose.model("Event", eventSchema);
