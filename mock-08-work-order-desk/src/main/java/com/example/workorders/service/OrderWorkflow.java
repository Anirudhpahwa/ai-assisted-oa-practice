package com.example.workorders.service;

import com.example.workorders.common.Actor;
import com.example.workorders.common.ApiException;
import com.example.workorders.model.Role;
import com.example.workorders.model.Status;
import com.example.workorders.model.WorkOrder;
import java.util.EnumSet;
import java.util.Map;
import java.util.Set;
import org.springframework.stereotype.Component;

/** The rules for moving a work order from one status to another. */
@Component
public class OrderWorkflow {

    private static final Map<Status, Set<Status>> ALLOWED = Map.of(
            Status.OPEN, EnumSet.of(Status.IN_PROGRESS, Status.CANCELLED),
            Status.IN_PROGRESS, EnumSet.of(Status.ON_HOLD, Status.DONE, Status.CANCELLED),
            Status.ON_HOLD, EnumSet.of(Status.CANCELLED),
            Status.DONE, EnumSet.noneOf(Status.class),
            Status.CANCELLED, EnumSet.noneOf(Status.class));

    public void check(WorkOrder order, Status next, Actor actor) {
        if (next == Status.CANCELLED && actor.role() != Role.MANAGER) {
            throw new ApiException(403, "only a manager can cancel");
        }
        if (!ALLOWED.get(order.getStatus()).contains(next)) {
            throw new ApiException(409, "invalid transition");
        }
        if (next == Status.IN_PROGRESS && order.getAssignee() == null) {
            throw new ApiException(409, "assignee required");
        }
    }
}
