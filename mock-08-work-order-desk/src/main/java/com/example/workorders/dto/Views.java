package com.example.workorders.dto;

import com.example.workorders.model.HistoryEntry;
import com.example.workorders.model.Part;
import com.example.workorders.model.WorkOrder;
import java.time.Instant;
import java.util.List;

public final class Views {

    private Views() {
    }

    public record OrderView(Long id, String title, String description, String location,
                            String priority, String status, String assignee, String createdBy,
                            Instant createdAt, Instant updatedAt) {

        public static OrderView of(WorkOrder order) {
            return new OrderView(order.getId(), order.getTitle(), order.getDescription(),
                    order.getLocation(), order.getPriority().name(), order.getStatus().name(),
                    order.getAssignee(), order.getCreatedBy(), order.getCreatedAt(),
                    order.getUpdatedAt());
        }
    }

    public record PageView<T>(List<T> items, int page, int size, long total, int totalPages) {
    }

    public record PartView(Long id, String name, int quantity, int unitCostCents) {

        public static PartView of(Part part) {
            return new PartView(part.getId(), part.getName(), part.getQuantity(),
                    part.getUnitCostCents());
        }
    }

    public record SummaryView(Long orderId, String status, int partLines, int totalQuantity,
                              long totalCostCents) {
    }

    public record HistoryView(String action, String detail, String actor, Instant at) {

        public static HistoryView of(HistoryEntry entry) {
            return new HistoryView(entry.getAction(), entry.getDetail(), entry.getActor(),
                    entry.getAt());
        }
    }
}
