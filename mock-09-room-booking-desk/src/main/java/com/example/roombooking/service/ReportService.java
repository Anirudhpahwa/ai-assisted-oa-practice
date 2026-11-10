package com.example.roombooking.service;

import com.example.roombooking.common.ApiException;
import com.example.roombooking.dto.Views.ReportView;
import com.example.roombooking.model.Booking;
import com.example.roombooking.model.BookingStatus;
import com.example.roombooking.model.Room;
import com.example.roombooking.repo.BookingRepository;
import java.time.Duration;
import java.time.Instant;
import java.time.YearMonth;
import java.time.ZoneOffset;
import java.time.format.DateTimeParseException;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ReportService {

    private final BookingRepository bookings;
    private final BookingService bookingService;

    public ReportService(BookingRepository bookings, BookingService bookingService) {
        this.bookings = bookings;
        this.bookingService = bookingService;
    }

    /** Usage and income of one room for the bookings that start in a UTC calendar month. */
    @Transactional(readOnly = true)
    public ReportView monthly(Long roomId, String monthText) {
        Room room = bookingService.requireRoom(roomId);
        YearMonth month = parse(monthText);
        Instant from = month.atDay(1).atStartOfDay().toInstant(ZoneOffset.UTC);
        Instant to = month.plusMonths(1).atDay(1).atStartOfDay().toInstant(ZoneOffset.UTC);
        List<Booking> inMonth = bookings
                .findByRoomIdAndStartsAtGreaterThanEqualAndStartsAtLessThan(room.getId(), from, to);

        int confirmed = 0;
        int cancelled = 0;
        long minutes = 0;
        long revenue = 0;
        for (Booking booking : inMonth) {
            if (booking.getStatus() == BookingStatus.CONFIRMED) {
                confirmed++;
                minutes += Duration.between(booking.getStartsAt(), booking.getEndsAt()).toMinutes();
                revenue += booking.getTotalCents();
            } else {
                cancelled++;
                revenue += booking.getTotalCents();
            }
        }
        return new ReportView(room.getId(), month.toString(), confirmed, cancelled, minutes, revenue);
    }

    private static YearMonth parse(String text) {
        try {
            return YearMonth.parse(text == null ? "" : text.trim());
        } catch (DateTimeParseException e) {
            throw new ApiException(400, "month must be a valid YYYY-MM month");
        }
    }
}
