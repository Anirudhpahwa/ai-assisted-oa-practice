package com.example.workorders.service;

import com.example.workorders.dto.ListQuery;
import com.example.workorders.model.Status;
import com.example.workorders.model.WorkOrder;
import jakarta.persistence.criteria.Predicate;
import java.util.ArrayList;
import java.util.List;
import org.springframework.data.jpa.domain.Specification;

public final class OrderSpecs {

    private OrderSpecs() {
    }

    /** Builds the filter for one list request. All conditions apply together. */
    public static Specification<WorkOrder> matching(ListQuery query) {
        return (root, cq, cb) -> {
            List<Predicate> all = new ArrayList<>();
            if (query.statuses() == null) {
                all.add(cb.notEqual(root.get("status"), Status.CANCELLED));
            } else {
                all.add(root.get("status").in(query.statuses()));
            }
            if (query.priority() != null) {
                all.add(cb.equal(root.get("priority"), query.priority()));
            }
            if (query.assignee() != null) {
                all.add(cb.equal(root.get("assignee"), query.assignee()));
            }
            if (!query.text().isEmpty()) {
                String pattern = "%" + escape(query.text()) + "%";
                Predicate inTitle = cb.like(cb.lower(root.get("title")), pattern, '\\');
                Predicate inDescription = cb.like(cb.lower(root.get("description")), pattern, '\\');
                all.add(cb.and(inTitle, inDescription));
            }
            return cb.and(all.toArray(new Predicate[0]));
        };
    }

    private static String escape(String text) {
        return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_");
    }
}
