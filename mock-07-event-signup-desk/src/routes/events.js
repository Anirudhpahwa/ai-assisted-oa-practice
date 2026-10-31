const express = require("express");
const { wrap } = require("../errors");
const { loadEvent, requireOrganizer } = require("../middleware/events");
const events = require("../controllers/eventController");
const registrations = require("../controllers/registrationController");
const summary = require("../controllers/summaryController");

const router = express.Router();

router.post("/", wrap(events.create));
router.get("/", wrap(events.list));
router.get("/:id", wrap(loadEvent), events.show);
router.patch("/:id", wrap(loadEvent), requireOrganizer, wrap(events.update));
router.get("/:id/summary", wrap(loadEvent), requireOrganizer, wrap(summary.show));
router.post("/:id/registrations", wrap(loadEvent), wrap(registrations.create));
router.delete("/:id/registrations/:regId", wrap(loadEvent), wrap(registrations.cancel));

module.exports = router;
