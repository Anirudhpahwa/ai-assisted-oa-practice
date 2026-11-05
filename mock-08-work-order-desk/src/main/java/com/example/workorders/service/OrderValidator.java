package com.example.workorders.service;

import com.example.workorders.common.ApiException;
import com.example.workorders.dto.ListQuery;
import com.example.workorders.model.Priority;
import com.example.workorders.model.Status;
import java.util.EnumSet;
import java.util.Locale;
import java.util.Set;
import org.springframework.stereotype.Component;

@Component
public class OrderValidator {

    private static ApiException bad(String message) {
        return new ApiException(400, message);
    }

    public String title(String raw) {
        String title = raw == null ? "" : raw;
        if (title.length() < 3 || title.length() > 100) {
            throw bad("title must be 3 to 100 characters");
        }
        return title.trim();
    }

    public String description(String raw) {
        String description = raw == null ? "" : raw.trim();
        if (description.length() > 500) {
            throw bad("description must be at most 500 characters");
        }
        return description;
    }

    public String location(String raw) {
        String location = raw == null ? "" : raw.trim();
        if (location.length() > 100) {
            throw bad("location must be at most 100 characters");
        }
        return location;
    }

    public Priority priority(String raw) {
        return Priority.parse(raw)
                .orElseThrow(() -> bad("priority must be URGENT, HIGH, MEDIUM or LOW"));
    }

    public String assignee(String raw) {
        String assignee = raw == null ? "" : raw.trim();
        if (assignee.isEmpty() || assignee.length() > 50) {
            throw bad("assignee must be 1 to 50 characters");
        }
        return assignee;
    }

    public Status status(String raw) {
        return Status.parse(raw)
                .orElseThrow(() -> bad("status must be one of OPEN, IN_PROGRESS, ON_HOLD, DONE, CANCELLED"));
    }

    public String note(String raw) {
        String note = raw == null ? "" : raw.trim();
        if (note.length() > 200) {
            throw bad("note must be at most 200 characters");
        }
        return note;
    }

    public String partName(String raw) {
        String name = raw == null ? "" : raw.trim();
        if (name.isEmpty() || name.length() > 60) {
            throw bad("name must be 1 to 60 characters");
        }
        return name;
    }

    public int quantity(Integer raw) {
        if (raw == null || raw < 1 || raw > 100) {
            throw bad("quantity must be an integer from 1 to 100");
        }
        return raw;
    }

    public int unitCostCents(Integer raw) {
        if (raw == null || raw < 0 || raw > 1_000_000) {
            throw bad("unitCostCents must be an integer from 0 to 1000000");
        }
        return raw;
    }

    /** Turns the raw query parameters of the list endpoint into typed filters and paging. */
    public ListQuery list(String status, String priority, String assignee, String q,
                          String page, String size, String sort) {
        Set<Status> statuses = blank(status) ? null : statusList(status);
        Priority wanted = blank(priority) ? null : priority(priority);
        String who = blank(assignee) ? null : assignee.trim();
        String text = q == null ? "" : q.trim().toLowerCase(Locale.ROOT);
        int pageNumber = whole(page, 1, 1, Integer.MAX_VALUE, "page must be a positive integer");
        int pageSize = whole(size, 10, 1, 50, "size must be an integer from 1 to 50");
        String order = blank(sort) ? "newest" : sort.trim().toLowerCase(Locale.ROOT);
        if (!order.equals("newest") && !order.equals("priority")) {
            throw bad("sort must be newest or priority");
        }
        return new ListQuery(statuses, wanted, who, text, pageNumber, pageSize, order);
    }

    private static boolean blank(String value) {
        return value == null || value.isBlank();
    }

    private Set<Status> statusList(String raw) {
        Set<Status> statuses = EnumSet.noneOf(Status.class);
        for (String part : raw.split(",", -1)) {
            statuses.add(Status.parse(part).orElseThrow(() -> bad(
                    "status must be a comma-separated list of OPEN, IN_PROGRESS, ON_HOLD, DONE, CANCELLED")));
        }
        return statuses;
    }

    private static int whole(String raw, int fallback, int min, int max, String message) {
        if (blank(raw)) {
            return fallback;
        }
        try {
            int value = Integer.parseInt(raw.trim());
            if (value < min || value > max || !raw.trim().matches("\\d+")) {
                throw bad(message);
            }
            return value;
        } catch (NumberFormatException e) {
            throw bad(message);
        }
    }
}
