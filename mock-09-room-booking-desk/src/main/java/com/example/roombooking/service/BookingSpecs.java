package com.example.roombooking.service;

import com.example.roombooking.dto.ListQuery;
import com.example.roombooking.model.Booking;
import jakarta.persistence.criteria.Predicate;
import java.util.ArrayList;
import java.util.List;
import org.springframework.data.jpa.domain.Specification;

public final class BookingSpecs {

    private BookingSpecs() {
    }

    /** Builds the filter for one list request. All conditions apply together. */
    public static Specification<Booking> matching(ListQuery query) {
        return (root, cq, cb) -> {
            List<Predicate> all = new ArrayList<>();
            if (query.roomId() != null) {
                all.add(cb.equal(root.get("roomId"), query.roomId()));
            }
            if (query.bookedBy() != null) {
                all.add(cb.equal(root.get("bookedBy"), query.bookedBy()));
            }
            if (query.status() != null) {
                all.add(cb.equal(root.get("status"), query.status()));
            }
            if (query.from() != null) {
                all.add(cb.greaterThanOrEqualTo(root.get("startsAt"), query.from()));
            }
            if (query.to() != null) {
                all.add(cb.lessThan(root.get("startsAt"), query.to()));
            }
            return cb.and(all.toArray(new Predicate[0]));
        };
    }
}
