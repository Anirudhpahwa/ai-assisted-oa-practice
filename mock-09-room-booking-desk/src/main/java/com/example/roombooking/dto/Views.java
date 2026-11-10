package com.example.roombooking.dto;

import com.example.roombooking.model.Booking;
import java.time.Instant;
import java.util.List;

public final class Views {

    private Views() {
    }

    public record BookingView(Long id, Long roomId, String bookedBy, String title, Instant startsAt,
                              Instant endsAt, int attendees, String status, long totalCents,
                              long feeCents, Instant createdAt, Instant cancelledAt) {

        public static BookingView of(Booking booking) {
            return new BookingView(booking.getId(), booking.getRoomId(), booking.getBookedBy(),
                    booking.getTitle(), booking.getStartsAt(), booking.getEndsAt(),
                    booking.getAttendees(), booking.getStatus().name(), booking.getTotalCents(),
                    booking.getFeeCents(), booking.getCreatedAt(), booking.getCancelledAt());
        }
    }

    public record PageView<T>(List<T> items, int page, int size, long totalElements, int totalPages) {
    }

    public record SlotView(Instant startsAt, Instant endsAt) {
    }

    public record AvailabilityView(Long roomId, String date, List<SlotView> free) {
    }

    public record ReportView(Long roomId, String month, int confirmedCount, int cancelledCount,
                             long bookedMinutes, long revenueCents) {
    }
}
