package com.example.roombooking.service;

import com.example.roombooking.common.Actor;
import com.example.roombooking.common.ApiException;
import com.example.roombooking.dto.ListQuery;
import com.example.roombooking.dto.Requests.CreateBooking;
import com.example.roombooking.dto.Views.BookingView;
import com.example.roombooking.dto.Views.PageView;
import com.example.roombooking.model.Booking;
import com.example.roombooking.model.BookingStatus;
import com.example.roombooking.model.Role;
import com.example.roombooking.model.Room;
import com.example.roombooking.repo.BookingRepository;
import com.example.roombooking.repo.RoomRepository;
import com.example.roombooking.service.BookingValidator.ValidBooking;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class BookingService {

    /** The outcome of a create call: {@code created} is false when an earlier booking was replayed. */
    public record CreateResult(Booking booking, boolean created) {
    }

    private final BookingRepository bookings;
    private final RoomRepository rooms;
    private final BookingValidator validator;
    private final CancellationPolicy policy;
    private final Clock clock;

    public BookingService(BookingRepository bookings, RoomRepository rooms, BookingValidator validator,
                          CancellationPolicy policy, Clock clock) {
        this.bookings = bookings;
        this.rooms = rooms;
        this.validator = validator;
        this.policy = policy;
        this.clock = clock;
    }

    /** An inactive room counts as not found. */
    public Room requireRoom(Long id) {
        return rooms.findById(id).filter(Room::isActive)
                .orElseThrow(() -> new ApiException(404, "room not found"));
    }

    public Booking require(Long id) {
        return bookings.findById(id).orElseThrow(() -> new ApiException(404, "booking not found"));
    }

    @Transactional
    public CreateResult create(Actor actor, String keyHeader, CreateBooking request) {
        String key = validator.idempotencyKey(keyHeader);
        if (key != null) {
            Optional<Booking> earlier = bookings.findByIdempotencyKey(key);
            if (earlier.isPresent()) {
                return new CreateResult(earlier.get(), false);
            }
        }
        ValidBooking valid = validator.create(request);
        Room room = requireRoom(valid.roomId());
        if (valid.attendees() > room.getCapacity()) {
            throw new ApiException(400, "attendees must not exceed the room capacity");
        }
        if (bookings.existsOverlap(room.getId(), BookingStatus.CONFIRMED, valid.start(), valid.end())) {
            throw new ApiException(409, "room is already booked for that time");
        }
        Booking booking = new Booking();
        booking.setRoomId(room.getId());
        booking.setBookedBy(actor.user());
        booking.setTitle(valid.title());
        booking.setStartsAt(valid.start());
        booking.setEndsAt(valid.end());
        booking.setAttendees(valid.attendees());
        booking.setStatus(BookingStatus.CONFIRMED);
        booking.setTotalCents(PriceCalculator.total(room.getHourlyRateCents(), valid.minutes()));
        booking.setFeeCents(0);
        booking.setIdempotencyKey(key);
        booking.setCreatedAt(clock.instant());
        return new CreateResult(bookings.save(booking), true);
    }

    @Transactional(readOnly = true)
    public PageView<BookingView> list(ListQuery query) {
        Sort sort = Sort.by(Sort.Order.asc("startsAt"), Sort.Order.asc("id"));
        Page<Booking> page = bookings.findAll(BookingSpecs.matching(query),
                PageRequest.of(query.page(), query.size(), sort));
        List<BookingView> items = page.getContent().stream().map(BookingView::of).toList();
        return new PageView<>(items, query.page(), query.size(), items.size(),
                page.getTotalPages());
    }

    @Transactional
    public Booking cancel(Long id, Actor actor) {
        Booking booking = require(id);
        if (!actor.user().equals(booking.getBookedBy()) && actor.role() != Role.MANAGER) {
            throw new ApiException(403, "only the booker or a manager can cancel");
        }
        if (booking.getStatus() == BookingStatus.CANCELLED) {
            throw new ApiException(409, "booking already cancelled");
        }
        Instant now = clock.instant();
        if (!now.isBefore(booking.getStartsAt())) {
            throw new ApiException(409, "booking has already started");
        }
        int percent = policy.feePercent(Duration.between(now, booking.getStartsAt()));
        booking.setFeeCents(PriceCalculator.percentOf(booking.getTotalCents(), percent));
        booking.setStatus(BookingStatus.CANCELLED);
        booking.setCancelledAt(now);
        return booking;
    }
}
