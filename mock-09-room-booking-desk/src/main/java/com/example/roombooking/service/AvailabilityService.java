package com.example.roombooking.service;

import com.example.roombooking.common.ApiException;
import com.example.roombooking.dto.Views.AvailabilityView;
import com.example.roombooking.dto.Views.SlotView;
import com.example.roombooking.model.Booking;
import com.example.roombooking.model.BookingStatus;
import com.example.roombooking.model.Room;
import com.example.roombooking.repo.BookingRepository;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AvailabilityService {

    private static final LocalTime OPEN = LocalTime.of(8, 0);
    private static final LocalTime CLOSE = LocalTime.of(20, 0);

    private final BookingRepository bookings;
    private final BookingService bookingService;

    public AvailabilityService(BookingRepository bookings, BookingService bookingService) {
        this.bookings = bookings;
        this.bookingService = bookingService;
    }

    /** The free windows of one room between opening and closing time on a UTC day. */
    @Transactional(readOnly = true)
    public AvailabilityView forDay(Long roomId, String dateText) {
        Room room = bookingService.requireRoom(roomId);
        LocalDate date = parse(dateText);
        Instant open = date.atTime(OPEN).toInstant(ZoneOffset.UTC);
        Instant close = date.atTime(CLOSE).toInstant(ZoneOffset.UTC);

        List<Booking> blocking = bookings
                .findByRoomIdAndStatusOrderByStartsAtAsc(room.getId(), BookingStatus.CONFIRMED).stream()
                .filter(b -> !b.getStartsAt().isBefore(open) && b.getStartsAt().isBefore(close))
                .toList();

        List<SlotView> free = new ArrayList<>();
        Instant cursor = open;
        for (Booking booking : blocking) {
            if (booking.getStartsAt().isAfter(cursor)) {
                free.add(new SlotView(cursor, booking.getStartsAt()));
            }
            if (booking.getEndsAt().isAfter(cursor)) {
                cursor = booking.getEndsAt();
            }
        }
        if (cursor.isBefore(close)) {
            free.add(new SlotView(cursor, close));
        }
        return new AvailabilityView(room.getId(), date.toString(), free);
    }

    private static LocalDate parse(String text) {
        try {
            return LocalDate.parse(text == null ? "" : text.trim());
        } catch (DateTimeParseException e) {
            throw new ApiException(400, "date must be a valid YYYY-MM-DD date");
        }
    }
}
