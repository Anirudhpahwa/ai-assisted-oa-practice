package com.example.roombooking.web;

import com.example.roombooking.common.Actor;
import com.example.roombooking.dto.Views.AvailabilityView;
import com.example.roombooking.dto.Views.ReportView;
import com.example.roombooking.service.AvailabilityService;
import com.example.roombooking.service.ReportService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/rooms")
public class RoomController {

    private static final String USER = "X-User";
    private static final String ROLE = "X-Role";

    private final AvailabilityService availability;
    private final ReportService reports;

    public RoomController(AvailabilityService availability, ReportService reports) {
        this.availability = availability;
        this.reports = reports;
    }

    @GetMapping("/{id}/availability")
    public AvailabilityView availability(
            @RequestHeader(value = USER, required = false) String user,
            @RequestHeader(value = ROLE, required = false) String role,
            @PathVariable Long id,
            @RequestParam(name = "date", required = false) String date) {
        Actor.from(user, role);
        return availability.forDay(id, date);
    }

    @GetMapping("/{id}/report")
    public ReportView report(
            @RequestHeader(value = USER, required = false) String user,
            @RequestHeader(value = ROLE, required = false) String role,
            @PathVariable Long id,
            @RequestParam(name = "month", required = false) String month) {
        Actor.from(user, role);
        return reports.monthly(id, month);
    }
}
