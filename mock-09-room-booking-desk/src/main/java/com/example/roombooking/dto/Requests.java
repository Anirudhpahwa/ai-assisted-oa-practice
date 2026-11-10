package com.example.roombooking.dto;

public final class Requests {

    private Requests() {
    }

    public record CreateBooking(Long roomId, String title, String startsAt, String endsAt,
                                Integer attendees) {
    }
}
