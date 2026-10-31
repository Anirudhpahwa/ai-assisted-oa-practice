const mongoose = require("mongoose");

const registrationSchema = new mongoose.Schema(
  {
    event: { type: mongoose.Schema.Types.ObjectId, ref: "Event", required: true, index: true },
    userId: { type: String, required: true },
    guests: { type: Number, default: 0 },
    seats: { type: Number, required: true },
    status: { type: String, enum: ["confirmed", "waitlisted", "cancelled"], required: true },
  },
  { timestamps: true }
);

module.exports = mongoose.model("Registration", registrationSchema);
