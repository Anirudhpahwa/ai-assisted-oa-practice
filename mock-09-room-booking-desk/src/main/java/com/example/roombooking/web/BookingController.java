package com.example.roombooking.web;

import com.example.roombooking.common.Actor;
import com.example.roombooking.dto.ListQuery;
import com.example.roombooking.dto.Requests.CreateBooking;
import com.example.roombooking.dto.Views.BookingView;
import com.example.roombooking.dto.Views.PageView;
import com.example.roombooking.service.BookingService;
import com.example.roombooking.service.BookingService.CreateResult;
import com.example.roombooking.service.BookingValidator;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/bookings")
public class BookingController {

    private static final String USER = "X-User";
    private static final String ROLE = "X-Role";
    private static final String KEY = "Idempotency-Key";

    private final BookingService service;
    private final BookingValidator validator;

    public BookingController(BookingService service, BookingValidator validator) {
        this.service = service;
        this.validator = validator;
    }

    @PostMapping
    public ResponseEntity<BookingView> create(
            @RequestHeader(value = USER, required = false) String user,
            @RequestHeader(value = ROLE, required = false) String role,
            @RequestHeader(value = KEY, required = false) String key,
            @RequestBody(required = false) CreateBooking body) {
        Actor actor = Actor.from(user, role);
        CreateBooking request = body == null ? new CreateBooking(null, null, null, null, null) : body;
        CreateResult result = service.create(actor, key, request);
        return ResponseEntity.status(201).body(BookingView.of(result.booking()));
    }

    @GetMapping
    public PageView<BookingView> list(
            @RequestHeader(value = USER, required = false) String user,
            @RequestHeader(value = ROLE, required = false) String role,
            @RequestParam(name = "room", required = false) String roomId,
            @RequestParam(name = "bookedBy", required = false) String bookedBy,
            @RequestParam(name = "status", required = false) String status,
            @RequestParam(name = "from", required = false) String from,
            @RequestParam(name = "to", required = false) String to,
            @RequestParam(name = "page", required = false) String page,
            @RequestParam(name = "size", required = false) String size) {
        Actor.from(user, role);
        ListQuery query = validator.list(roomId, bookedBy, status, from, to, page, size);
        return service.list(query);
    }

    @GetMapping("/{id}")
    public BookingView show(
            @RequestHeader(value = USER, required = false) String user,
            @RequestHeader(value = ROLE, required = false) String role,
            @PathVariable Long id) {
        Actor.from(user, role);
        return BookingView.of(service.require(id));
    }

    @PostMapping("/{id}/cancel")
    public BookingView cancel(
            @RequestHeader(value = USER, required = false) String user,
            @RequestHeader(value = ROLE, required = false) String role,
            @PathVariable Long id) {
        Actor actor = Actor.from(user, role);
        return BookingView.of(service.cancel(id, actor));
    }
}
