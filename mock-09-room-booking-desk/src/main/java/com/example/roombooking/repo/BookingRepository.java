package com.example.roombooking.repo;

import com.example.roombooking.model.Booking;
import com.example.roombooking.model.BookingStatus;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface BookingRepository
        extends JpaRepository<Booking, Long>, JpaSpecificationExecutor<Booking> {

    @Query("select count(b) > 0 from Booking b where b.roomId = :roomId and b.status = :status "
            + "and b.startsAt <= :end and b.endsAt >= :start")
    boolean existsOverlap(@Param("roomId") Long roomId, @Param("status") BookingStatus status,
                          @Param("start") Instant start, @Param("end") Instant end);

    Optional<Booking> findByIdempotencyKey(String idempotencyKey);

    List<Booking> findByRoomIdAndStatusOrderByStartsAtAsc(Long roomId, BookingStatus status);

    List<Booking> findByRoomIdAndStartsAtGreaterThanEqualAndStartsAtLessThan(
            Long roomId, Instant from, Instant to);
}
