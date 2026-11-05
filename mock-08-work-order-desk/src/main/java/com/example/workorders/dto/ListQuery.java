package com.example.workorders.dto;

import com.example.workorders.model.Priority;
import com.example.workorders.model.Status;
import java.util.Set;

/** Parsed query string of GET /api/orders. {@code statuses} is null when no status was asked for. */
public record ListQuery(Set<Status> statuses, Priority priority, String assignee, String text,
                        int page, int size, String sort) {
}
