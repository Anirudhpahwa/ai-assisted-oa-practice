package com.example.roombooking;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.request;

import com.example.roombooking.model.Booking;
import com.example.roombooking.model.BookingStatus;
import com.example.roombooking.model.Room;
import com.example.roombooking.repo.BookingRepository;
import com.example.roombooking.repo.RoomRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.NullNode;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder;

@SpringBootTest
@AutoConfigureMockMvc
class BookingApiTest {

    /** The moment the application believes it is during every test. */
    static final Instant NOW = Instant.parse("2027-03-01T12:00:00Z");

    @TestConfiguration
    static class FixedClock {
        @Bean
        @Primary
        Clock testClock() {
            return Clock.fixed(NOW, ZoneOffset.UTC);
        }
    }

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper json;
    @Autowired RoomRepository rooms;
    @Autowired BookingRepository bookings;

    record Resp(int status, JsonNode body) {
        String text(String field) {
            return body.get(field).asText();
        }
    }

    @BeforeEach
    void clean() {
        bookings.deleteAll();
        rooms.deleteAll();
    }

    Resp call(String method, String path, String user, String role, Object body, Map<String, String> headers)
            throws Exception {
        MockHttpServletRequestBuilder req = request(HttpMethod.valueOf(method), path);
        if (user != null) {
            req.header("X-User", user);
        }
        if (role != null) {
            req.header("X-Role", role);
        }
        headers.forEach(req::header);
        if (body != null) {
            req.contentType(MediaType.APPLICATION_JSON).content(json.writeValueAsString(body));
        }
        MvcResult result = mvc.perform(req).andReturn();
        String text = result.getResponse().getContentAsString();
        return new Resp(result.getResponse().getStatus(), text.isEmpty() ? NullNode.getInstance() : json.readTree(text));
    }

    Resp call(String method, String path, String user, String role, Object body) throws Exception {
        return call(method, path, user, role, body, Map.of());
    }

    Resp get(String path, String user) throws Exception {
        return call("GET", path, user, null, null);
    }

    Map<String, Object> body(Long roomId, String title, String start, String end, Integer attendees) {
        Map<String, Object> body = new HashMap<>();
        body.put("roomId", roomId);
        body.put("title", title);
        body.put("startsAt", start);
        body.put("endsAt", end);
        body.put("attendees", attendees);
        return body;
    }

    Booking seed(Room room, String user, String title, Instant start, Instant end, BookingStatus status,
                 long total, long fee) {
        Booking booking = new Booking();
        booking.setRoomId(room.getId());
        booking.setBookedBy(user);
        booking.setTitle(title);
        booking.setStartsAt(start);
        booking.setEndsAt(end);
        booking.setAttendees(2);
        booking.setStatus(status);
        booking.setTotalCents(total);
        booking.setFeeCents(fee);
        booking.setCreatedAt(NOW);
        return bookings.save(booking);
    }

    Booking seed(Room room, String user, String title, String start, String end, BookingStatus status) {
        return seed(room, user, title, Instant.parse(start), Instant.parse(end), status, 1000, 0);
    }

    Booking startingIn(Room room, String user, long minutes, long total) {
        Instant start = NOW.plus(Duration.ofMinutes(minutes));
        return seed(room, user, "Booking in " + minutes, start, start.plus(Duration.ofHours(1)),
                BookingStatus.CONFIRMED, total, 0);
    }

    List<String> titles(Resp response) {
        List<String> titles = new ArrayList<>();
        for (JsonNode item : response.body().get("items")) {
            titles.add(item.get("title").asText());
        }
        return titles;
    }

    List<String> slots(Resp response) {
        List<String> slots = new ArrayList<>();
        for (JsonNode slot : response.body().get("free")) {
            slots.add(slot.get("startsAt").asText() + "/" + slot.get("endsAt").asText());
        }
        return slots;
    }

    @Test
    void createBooking() throws Exception {
        Room aspen = rooms.save(new Room("Aspen", 8, 5000, true));
        Room birch = rooms.save(new Room("Birch", 4, 3333, true));
        Room cedar = rooms.save(new Room("Cedar", 6, 4000, false));

        Resp r = call("POST", "/api/bookings", null, null,
                body(aspen.getId(), "Sprint planning", "2027-03-02T09:00:00Z", "2027-03-02T10:30:00Z", 5));
        assertEquals(401, r.status());
        assertEquals("X-User header required", r.text("error"));
        r = call("POST", "/api/bookings", "ana", "ADMIN",
                body(aspen.getId(), "Sprint planning", "2027-03-02T09:00:00Z", "2027-03-02T10:30:00Z", 5));
        assertEquals(400, r.status());
        assertEquals("role must be USER or MANAGER", r.text("error"));

        r = call("POST", "/api/bookings", "ana", null,
                body(aspen.getId(), " Sprint planning ", "2027-03-02T09:00:00Z", "2027-03-02T10:30:00Z", 5));
        assertEquals(201, r.status());
        assertEquals("Sprint planning", r.text("title"));
        assertEquals("CONFIRMED", r.text("status"));
        assertEquals("ana", r.text("bookedBy"));
        assertEquals(aspen.getId().longValue(), r.body().get("roomId").asLong());
        assertEquals("2027-03-02T09:00:00Z", r.text("startsAt"));
        assertEquals("2027-03-02T10:30:00Z", r.text("endsAt"));
        assertEquals(5, r.body().get("attendees").asInt());
        assertEquals(7500L, r.body().get("totalCents").asLong());
        assertEquals(0L, r.body().get("feeCents").asLong());
        assertEquals(NullNode.getInstance(), r.body().get("cancelledAt"));

        r = call("POST", "/api/bookings", "ana", null,
                body(birch.getId(), "Quick sync", "2027-03-02T09:00:00Z", "2027-03-02T09:30:00Z", 2));
        assertEquals(201, r.status());
        assertEquals(1667L, r.body().get("totalCents").asLong());
        r = call("POST", "/api/bookings", "ana", null,
                body(birch.getId(), "Workshop", "2027-03-02T09:30:00Z", "2027-03-02T11:00:00Z", 2));
        assertEquals(201, r.status());
        assertEquals(5000L, r.body().get("totalCents").asLong());

        r = call("POST", "/api/bookings", "bob", null,
                body(aspen.getId(), "Design review", "2027-03-02T10:30:00Z", "2027-03-02T11:30:00Z", 4));
        assertEquals(201, r.status());
        for (String[] clash : new String[][] {
                {"2027-03-02T10:00:00Z", "2027-03-02T11:00:00Z"},
                {"2027-03-02T09:00:00Z", "2027-03-02T09:30:00Z"},
                {"2027-03-02T08:00:00Z", "2027-03-02T12:00:00Z"}}) {
            r = call("POST", "/api/bookings", "bob", null, body(aspen.getId(), "Clash", clash[0], clash[1], 2));
            assertEquals(409, r.status());
            assertEquals("room is already booked for that time", r.text("error"));
        }

        seed(aspen, "zed", "Called off", "2027-03-02T14:00:00Z", "2027-03-02T15:00:00Z", BookingStatus.CANCELLED);
        r = call("POST", "/api/bookings", "ana", null,
                body(aspen.getId(), "Retro", "2027-03-02T14:00:00Z", "2027-03-02T15:00:00Z", 3));
        assertEquals(201, r.status());

        r = call("POST", "/api/bookings", "ana", null,
                body(aspen.getId(), "Offsite call", "2027-03-03T10:00:00+01:00", "2027-03-03T11:00:00+01:00", 3));
        assertEquals(201, r.status());
        assertEquals("2027-03-03T09:00:00Z", r.text("startsAt"));

        r = call("POST", "/api/bookings", "ana", null,
                body(aspen.getId(), "All day", "2027-03-05T08:00:00Z", "2027-03-05T16:00:00Z", 8));
        assertEquals(201, r.status());
        assertEquals(40000L, r.body().get("totalCents").asLong());

        String day = "2027-03-06T09:00:00Z";
        String dayEnd = "2027-03-06T10:00:00Z";
        r = call("POST", "/api/bookings", "ana", null, body(aspen.getId(), "ab", day, dayEnd, 2));
        assertEquals(400, r.status());
        assertEquals("title must be 3 to 80 characters", r.text("error"));
        r = call("POST", "/api/bookings", "ana", null, body(null, "Planning", day, dayEnd, 2));
        assertEquals(400, r.status());
        assertEquals("roomId is required", r.text("error"));
        r = call("POST", "/api/bookings", "ana", null, body(aspen.getId(), "Planning", "tomorrow", dayEnd, 2));
        assertEquals(400, r.status());
        assertEquals("startsAt must be a valid date-time", r.text("error"));
        r = call("POST", "/api/bookings", "ana", null, body(aspen.getId(), "Planning", day, "soon", 2));
        assertEquals(400, r.status());
        assertEquals("endsAt must be a valid date-time", r.text("error"));
        for (String end : List.of(day, "2027-03-06T08:30:00Z")) {
            r = call("POST", "/api/bookings", "ana", null, body(aspen.getId(), "Planning", day, end, 2));
            assertEquals(400, r.status());
            assertEquals("endsAt must be after startsAt", r.text("error"));
        }
        for (String end : List.of("2027-03-06T09:45:00Z", "2027-03-06T09:15:00Z", "2027-03-06T17:30:00Z")) {
            r = call("POST", "/api/bookings", "ana", null, body(aspen.getId(), "Planning", day, end, 2));
            assertEquals(400, r.status());
            assertEquals("duration must be 30 minutes to 8 hours in 30-minute steps", r.text("error"));
        }
        for (Integer attendees : new Integer[] {0, null}) {
            r = call("POST", "/api/bookings", "ana", null, body(aspen.getId(), "Planning", day, dayEnd, attendees));
            assertEquals(400, r.status());
            assertEquals("attendees must be a whole number of 1 or more", r.text("error"));
        }
        r = call("POST", "/api/bookings", "ana", null, body(aspen.getId(), "Planning", day, dayEnd, 9));
        assertEquals(400, r.status());
        assertEquals("attendees must not exceed the room capacity", r.text("error"));
        r = call("POST", "/api/bookings", "ana", null, body(aspen.getId(), "Planning", day, dayEnd, 8));
        assertEquals(201, r.status());

        r = call("POST", "/api/bookings", "ana", null, body(999999L, "Planning", day, dayEnd, 2));
        assertEquals(404, r.status());
        assertEquals("room not found", r.text("error"));
        r = call("POST", "/api/bookings", "ana", null, body(cedar.getId(), "Planning", day, dayEnd, 2));
        assertEquals(404, r.status());

        assertEquals(9, bookings.count());
    }

    @Test
    void idempotentCreate() throws Exception {
        Room aspen = rooms.save(new Room("Aspen", 8, 5000, true));
        Room birch = rooms.save(new Room("Birch", 4, 3333, true));
        Map<String, Object> standup = body(aspen.getId(), "Standup", "2027-03-02T09:00:00Z", "2027-03-02T09:30:00Z", 3);

        Resp first = call("POST", "/api/bookings", "ana", null, standup, Map.of("Idempotency-Key", "key-1"));
        assertEquals(201, first.status());
        long id = first.body().get("id").asLong();

        Resp r = call("POST", "/api/bookings", "ana", null, standup, Map.of("Idempotency-Key", "key-1"));
        assertEquals(200, r.status());
        assertEquals(id, r.body().get("id").asLong());
        assertEquals(1, bookings.count());

        r = call("POST", "/api/bookings", "ana", null,
                body(aspen.getId(), "Different", "2027-03-02T10:00:00Z", "2027-03-02T11:00:00Z", 2),
                Map.of("Idempotency-Key", " key-1 "));
        assertEquals(200, r.status());
        assertEquals(id, r.body().get("id").asLong());
        assertEquals("2027-03-02T09:00:00Z", r.text("startsAt"));
        assertEquals("Standup", r.text("title"));

        r = call("POST", "/api/bookings", "ana", null,
                body(aspen.getId(), "x", "nonsense", "nonsense", 0), Map.of("Idempotency-Key", "key-1"));
        assertEquals(200, r.status());
        assertEquals(id, r.body().get("id").asLong());

        r = call("POST", "/api/bookings", "bob", null,
                body(birch.getId(), "Interview", "2027-03-02T09:00:00Z", "2027-03-02T10:00:00Z", 2),
                Map.of("Idempotency-Key", "key-1"));
        assertEquals(201, r.status());
        assertEquals("bob", r.text("bookedBy"));
        long bobId = r.body().get("id").asLong();
        assertEquals(2, bookings.count());
        r = call("POST", "/api/bookings", "bob", null,
                body(birch.getId(), "Interview", "2027-03-02T09:00:00Z", "2027-03-02T10:00:00Z", 2),
                Map.of("Idempotency-Key", "key-1"));
        assertEquals(200, r.status());
        assertEquals(bobId, r.body().get("id").asLong());

        r = call("POST", "/api/bookings", "ana", null, standup, Map.of("Idempotency-Key", "  "));
        assertEquals(409, r.status());
        Map<String, Object> lunch = body(aspen.getId(), "Lunch", "2027-03-02T12:00:00Z", "2027-03-02T13:00:00Z", 3);
        r = call("POST", "/api/bookings", "ana", null, lunch, Map.of("Idempotency-Key", "  "));
        assertEquals(201, r.status());
        r = call("POST", "/api/bookings", "ana", null, lunch, Map.of("Idempotency-Key", "  "));
        assertEquals(409, r.status());

        Map<String, Object> demo = body(aspen.getId(), "Demo", "2027-03-02T14:00:00Z", "2027-03-02T15:00:00Z", 3);
        r = call("POST", "/api/bookings", "ana", null, demo, Map.of("Idempotency-Key", "k".repeat(65)));
        assertEquals(400, r.status());
        assertEquals("Idempotency-Key must be at most 64 characters", r.text("error"));
        r = call("POST", "/api/bookings", "ana", null, demo, Map.of("Idempotency-Key", "k".repeat(64)));
        assertEquals(201, r.status());

        assertEquals(4, bookings.count());
    }

    @Test
    void listBookings() throws Exception {
        Room aspen = rooms.save(new Room("Aspen", 8, 5000, true));
        Room birch = rooms.save(new Room("Birch", 4, 3333, true));
        seed(aspen, "ana", "b1", "2027-03-02T09:00:00Z", "2027-03-02T10:00:00Z", BookingStatus.CONFIRMED);
        seed(aspen, "bob", "b2", "2027-03-02T10:00:00Z", "2027-03-02T11:00:00Z", BookingStatus.CONFIRMED);
        seed(birch, "ana", "b3", "2027-03-02T09:00:00Z", "2027-03-02T09:30:00Z", BookingStatus.CANCELLED);
        seed(birch, "bob", "b4", "2027-03-03T14:00:00Z", "2027-03-03T15:00:00Z", BookingStatus.CONFIRMED);
        seed(aspen, "ana", "b5", "2027-03-04T09:00:00Z", "2027-03-04T10:00:00Z", BookingStatus.CONFIRMED);
        seed(birch, "ana", "b6", "2027-03-05T09:00:00Z", "2027-03-05T10:00:00Z", BookingStatus.CONFIRMED);

        Resp r = get("/api/bookings", "kim");
        assertEquals(200, r.status());
        assertEquals(List.of("b1", "b3", "b2", "b4", "b5", "b6"), titles(r));
        assertEquals(0, r.body().get("page").asInt());
        assertEquals(20, r.body().get("size").asInt());
        assertEquals(6, r.body().get("totalElements").asInt());
        assertEquals(1, r.body().get("totalPages").asInt());

        r = get("/api/bookings?roomId=" + aspen.getId(), "kim");
        assertEquals(List.of("b1", "b2", "b5"), titles(r));
        r = get("/api/bookings?bookedBy=ana", "kim");
        assertEquals(List.of("b1", "b3", "b5", "b6"), titles(r));
        r = get("/api/bookings?status=cancelled", "kim");
        assertEquals(List.of("b3"), titles(r));
        r = get("/api/bookings?status=confirmed&bookedBy=ana", "kim");
        assertEquals(List.of("b1", "b5", "b6"), titles(r));
        r = get("/api/bookings?roomId=" + aspen.getId() + "&bookedBy=ana", "kim");
        assertEquals(List.of("b1", "b5"), titles(r));

        r = get("/api/bookings?from=2027-03-03T00:00:00Z&to=2027-03-05T09:00:00Z", "kim");
        assertEquals(List.of("b4", "b5"), titles(r));
        r = get("/api/bookings?from=2027-03-04T09:00:00Z", "kim");
        assertEquals(List.of("b5", "b6"), titles(r));

        r = get("/api/bookings?size=2&page=0", "kim");
        assertEquals(List.of("b1", "b3"), titles(r));
        assertEquals(6, r.body().get("totalElements").asInt());
        assertEquals(3, r.body().get("totalPages").asInt());
        r = get("/api/bookings?size=2&page=1", "kim");
        assertEquals(List.of("b2", "b4"), titles(r));
        assertEquals(1, r.body().get("page").asInt());
        assertEquals(2, r.body().get("size").asInt());
        r = get("/api/bookings?size=4&page=1", "kim");
        assertEquals(List.of("b5", "b6"), titles(r));
        assertEquals(6, r.body().get("totalElements").asInt());
        assertEquals(2, r.body().get("totalPages").asInt());
        r = get("/api/bookings?size=2&page=3", "kim");
        assertEquals(List.of(), titles(r));
        assertEquals(6, r.body().get("totalElements").asInt());

        for (String bad : List.of("page=-1", "page=x")) {
            r = get("/api/bookings?" + bad, "kim");
            assertEquals(400, r.status());
            assertEquals("page must be zero or a positive integer", r.text("error"));
        }
        for (String bad : List.of("size=0", "size=101")) {
            r = get("/api/bookings?" + bad, "kim");
            assertEquals(400, r.status());
            assertEquals("size must be an integer from 1 to 100", r.text("error"));
        }
        r = get("/api/bookings?status=pending", "kim");
        assertEquals(400, r.status());
        assertEquals("status must be CONFIRMED or CANCELLED", r.text("error"));
        r = get("/api/bookings?roomId=abc", "kim");
        assertEquals(400, r.status());
        assertEquals("roomId must be a whole number", r.text("error"));
        r = get("/api/bookings?from=yesterday", "kim");
        assertEquals(400, r.status());
        assertEquals("from must be a valid date-time", r.text("error"));
        r = get("/api/bookings?from=2027-03-05T00:00:00Z&to=2027-03-05T00:00:00Z", "kim");
        assertEquals(400, r.status());
        assertEquals("from must be before to", r.text("error"));
    }

    @Test
    void cancelBooking() throws Exception {
        Room aspen = rooms.save(new Room("Aspen", 8, 5000, true));

        Booking early = startingIn(aspen, "ana", 2880, 10000);
        Resp r = call("POST", "/api/bookings/" + early.getId() + "/cancel", "ana", null, null);
        assertEquals(200, r.status());
        assertEquals("CANCELLED", r.text("status"));
        assertEquals(0L, r.body().get("feeCents").asLong());
        assertEquals("2027-03-01T12:00:00Z", r.text("cancelledAt"));
        Booking saved = bookings.findById(early.getId()).orElseThrow();
        assertEquals(BookingStatus.CANCELLED, saved.getStatus());
        assertEquals(0L, saved.getFeeCents());

        r = call("POST", "/api/bookings/" + early.getId() + "/cancel", "ana", null, null);
        assertEquals(409, r.status());
        assertEquals("booking already cancelled", r.text("error"));

        long[][] cases = {{1440, 0}, {1380, 5000}, {120, 5000}, {150, 5000}, {60, 10000}};
        for (long[] c : cases) {
            Booking booking = startingIn(aspen, "ana", c[0], 10000);
            r = call("POST", "/api/bookings/" + booking.getId() + "/cancel", "ana", null, null);
            assertEquals(200, r.status());
            assertEquals(c[1], r.body().get("feeCents").asLong());
        }

        Booking odd = startingIn(aspen, "ana", 150, 3333);
        r = call("POST", "/api/bookings/" + odd.getId() + "/cancel", "ana", null, null);
        assertEquals(1667L, r.body().get("feeCents").asLong());

        for (long minutes : new long[] {-60, 0}) {
            Booking started = startingIn(aspen, "ana", minutes, 10000);
            r = call("POST", "/api/bookings/" + started.getId() + "/cancel", "ana", null, null);
            assertEquals(409, r.status());
            assertEquals("booking has already started", r.text("error"));
        }

        Booking mine = startingIn(aspen, "ana", 600, 10000);
        r = call("POST", "/api/bookings/" + mine.getId() + "/cancel", "zed", null, null);
        assertEquals(403, r.status());
        assertEquals("only the booker or a manager can cancel", r.text("error"));
        assertEquals(BookingStatus.CONFIRMED, bookings.findById(mine.getId()).orElseThrow().getStatus());
        r = call("POST", "/api/bookings/" + mine.getId() + "/cancel", "kim", "manager", null);
        assertEquals(200, r.status());
        assertEquals(5000L, r.body().get("feeCents").asLong());

        r = call("POST", "/api/bookings/999999/cancel", "ana", null, null);
        assertEquals(404, r.status());
        assertEquals("booking not found", r.text("error"));
        r = call("POST", "/api/bookings/" + mine.getId() + "/cancel", null, null, null);
        assertEquals(401, r.status());
    }

    @Test
    void roomAvailability() throws Exception {
        Room aspen = rooms.save(new Room("Aspen", 8, 5000, true));
        Room birch = rooms.save(new Room("Birch", 4, 3333, true));
        Room cedar = rooms.save(new Room("Cedar", 6, 4000, false));
        seed(aspen, "ana", "early", "2027-03-02T07:00:00Z", "2027-03-02T09:00:00Z", BookingStatus.CONFIRMED);
        seed(aspen, "ana", "before open", "2027-03-02T06:00:00Z", "2027-03-02T08:00:00Z", BookingStatus.CONFIRMED);
        seed(aspen, "bob", "midday", "2027-03-02T11:00:00Z", "2027-03-02T12:30:00Z", BookingStatus.CONFIRMED);
        seed(aspen, "bob", "next", "2027-03-02T12:30:00Z", "2027-03-02T13:00:00Z", BookingStatus.CONFIRMED);
        seed(aspen, "bob", "late", "2027-03-02T18:30:00Z", "2027-03-02T20:30:00Z", BookingStatus.CONFIRMED);
        seed(aspen, "bob", "called off", "2027-03-02T14:00:00Z", "2027-03-02T15:00:00Z", BookingStatus.CANCELLED);
        seed(aspen, "ana", "other day", "2027-03-03T09:00:00Z", "2027-03-03T10:00:00Z", BookingStatus.CONFIRMED);
        seed(birch, "ana", "other room", "2027-03-02T10:00:00Z", "2027-03-02T11:00:00Z", BookingStatus.CONFIRMED);

        Resp r = get("/api/rooms/" + aspen.getId() + "/availability?date=2027-03-02", "kim");
        assertEquals(200, r.status());
        assertEquals(aspen.getId().longValue(), r.body().get("roomId").asLong());
        assertEquals("2027-03-02", r.text("date"));
        assertEquals(List.of("2027-03-02T09:00:00Z/2027-03-02T11:00:00Z",
                "2027-03-02T13:00:00Z/2027-03-02T18:30:00Z"), slots(r));

        r = get("/api/rooms/" + aspen.getId() + "/availability?date=2027-03-03", "kim");
        assertEquals(List.of("2027-03-03T08:00:00Z/2027-03-03T09:00:00Z",
                "2027-03-03T10:00:00Z/2027-03-03T20:00:00Z"), slots(r));
        r = get("/api/rooms/" + aspen.getId() + "/availability?date=2027-03-04", "kim");
        assertEquals(List.of("2027-03-04T08:00:00Z/2027-03-04T20:00:00Z"), slots(r));
        r = get("/api/rooms/" + birch.getId() + "/availability?date=2027-03-02", "kim");
        assertEquals(List.of("2027-03-02T08:00:00Z/2027-03-02T10:00:00Z",
                "2027-03-02T11:00:00Z/2027-03-02T20:00:00Z"), slots(r));

        for (String query : List.of("?date=2027-13-01", "?date=2027-3-2", "")) {
            r = get("/api/rooms/" + aspen.getId() + "/availability" + query, "kim");
            assertEquals(400, r.status());
            assertEquals("date must be a valid YYYY-MM-DD date", r.text("error"));
        }
        r = get("/api/rooms/999999/availability?date=nonsense", "kim");
        assertEquals(404, r.status());
        assertEquals("room not found", r.text("error"));
        r = get("/api/rooms/" + cedar.getId() + "/availability?date=2027-03-02", "kim");
        assertEquals(404, r.status());
        r = get("/api/rooms/" + aspen.getId() + "/availability?date=2027-03-02", null);
        assertEquals(401, r.status());
    }

    @Test
    void monthlyReport() throws Exception {
        Room aspen = rooms.save(new Room("Aspen", 8, 5000, true));
        Room birch = rooms.save(new Room("Birch", 4, 3333, true));
        seed(aspen, "ana", "first minute", Instant.parse("2027-03-01T00:00:00Z"),
                Instant.parse("2027-03-01T00:30:00Z"), BookingStatus.CONFIRMED, 2500, 0);
        seed(aspen, "ana", "planning", Instant.parse("2027-03-02T09:00:00Z"),
                Instant.parse("2027-03-02T10:30:00Z"), BookingStatus.CONFIRMED, 7500, 0);
        seed(aspen, "bob", "last day", Instant.parse("2027-03-31T20:00:00Z"),
                Instant.parse("2027-03-31T22:00:00Z"), BookingStatus.CONFIRMED, 10000, 0);
        seed(aspen, "bob", "next month", Instant.parse("2027-04-01T00:00:00Z"),
                Instant.parse("2027-04-01T01:00:00Z"), BookingStatus.CONFIRMED, 9999, 0);
        seed(aspen, "bob", "last month", Instant.parse("2027-02-28T23:00:00Z"),
                Instant.parse("2027-03-01T01:00:00Z"), BookingStatus.CONFIRMED, 9999, 0);
        seed(aspen, "ana", "late cancel", Instant.parse("2027-03-10T09:00:00Z"),
                Instant.parse("2027-03-10T10:00:00Z"), BookingStatus.CANCELLED, 5000, 2500);
        seed(aspen, "ana", "free cancel", Instant.parse("2027-03-11T09:00:00Z"),
                Instant.parse("2027-03-11T10:00:00Z"), BookingStatus.CANCELLED, 6000, 0);
        seed(birch, "ana", "other room", Instant.parse("2027-03-05T09:00:00Z"),
                Instant.parse("2027-03-05T10:00:00Z"), BookingStatus.CONFIRMED, 777, 0);

        Resp r = get("/api/rooms/" + aspen.getId() + "/report?month=2027-03", "kim");
        assertEquals(200, r.status());
        assertEquals(aspen.getId().longValue(), r.body().get("roomId").asLong());
        assertEquals("2027-03", r.text("month"));
        assertEquals(3, r.body().get("confirmedCount").asInt());
        assertEquals(2, r.body().get("cancelledCount").asInt());
        assertEquals(240L, r.body().get("bookedMinutes").asLong());
        assertEquals(22500L, r.body().get("revenueCents").asLong());

        r = get("/api/rooms/" + birch.getId() + "/report?month=2027-03", "kim");
        assertEquals(1, r.body().get("confirmedCount").asInt());
        assertEquals(60L, r.body().get("bookedMinutes").asLong());
        assertEquals(777L, r.body().get("revenueCents").asLong());

        r = get("/api/rooms/" + aspen.getId() + "/report?month=2027-05", "kim");
        assertEquals(0, r.body().get("confirmedCount").asInt());
        assertEquals(0, r.body().get("cancelledCount").asInt());
        assertEquals(0L, r.body().get("bookedMinutes").asLong());
        assertEquals(0L, r.body().get("revenueCents").asLong());

        for (String query : List.of("?month=2027-3", "?month=2027-13", "?month=March", "")) {
            r = get("/api/rooms/" + aspen.getId() + "/report" + query, "kim");
            assertEquals(400, r.status());
            assertEquals("month must be a valid YYYY-MM month", r.text("error"));
        }
        r = get("/api/rooms/999999/report?month=2027-03", "kim");
        assertEquals(404, r.status());
        assertEquals("room not found", r.text("error"));
        r = get("/api/rooms/" + aspen.getId() + "/report?month=2027-03", null);
        assertEquals(401, r.status());
    }
}
