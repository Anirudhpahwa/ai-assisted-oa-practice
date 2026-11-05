package com.example.workorders.service;

import com.example.workorders.common.Actor;
import com.example.workorders.common.ApiException;
import com.example.workorders.dto.ListQuery;
import com.example.workorders.dto.Requests.CreateOrder;
import com.example.workorders.dto.Requests.Transition;
import com.example.workorders.dto.Requests.UpdateOrder;
import com.example.workorders.dto.Views.OrderView;
import com.example.workorders.dto.Views.PageView;
import com.example.workorders.model.Priority;
import com.example.workorders.model.Role;
import com.example.workorders.model.Status;
import com.example.workorders.model.WorkOrder;
import com.example.workorders.repo.WorkOrderRepository;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderService {

    private final WorkOrderRepository orders;
    private final OrderValidator validator;
    private final OrderWorkflow workflow;
    private final HistoryService history;

    public OrderService(WorkOrderRepository orders, OrderValidator validator, OrderWorkflow workflow,
                        HistoryService history) {
        this.orders = orders;
        this.validator = validator;
        this.workflow = workflow;
        this.history = history;
    }

    public WorkOrder require(Long id) {
        return orders.findById(id).orElseThrow(() -> new ApiException(404, "work order not found"));
    }

    @Transactional
    public WorkOrder create(CreateOrder request, Actor actor) {
        WorkOrder order = new WorkOrder();
        order.setTitle(validator.title(request.title()));
        order.setDescription(validator.description(request.description()));
        order.setLocation(validator.location(request.location()));
        order.setPriority(request.priority() == null ? Priority.MEDIUM : validator.priority(request.priority()));
        order.setStatus(Status.OPEN);
        order.setCreatedBy(actor.user());
        Instant now = Instant.now();
        order.setCreatedAt(now);
        order.setUpdatedAt(now);
        orders.save(order);
        history.record(order.getId(), "CREATED", "created", actor.user());
        return order;
    }

    @Transactional(readOnly = true)
    public PageView<OrderView> list(ListQuery query) {
        Sort sort = query.sort().equals("priority")
                ? Sort.by(Sort.Order.asc("priority"), Sort.Order.asc("createdAt"), Sort.Order.asc("id"))
                : Sort.by(Sort.Order.desc("createdAt"), Sort.Order.desc("id"));
        PageRequest pageRequest = PageRequest.of(query.page() - 1, query.size(), sort);
        Page<WorkOrder> page = orders.findAll(OrderSpecs.matching(query), pageRequest);
        List<OrderView> items = page.getContent().stream().map(OrderView::of).toList();
        return new PageView<>(items, query.page(), query.size(), page.getTotalElements(), page.getTotalPages());
    }

    @Transactional
    public WorkOrder update(Long id, UpdateOrder request, Actor actor) {
        WorkOrder order = require(id);
        if (request.title() == null && request.description() == null && request.location() == null
                && request.priority() == null && request.assignee() == null) {
            throw new ApiException(400, "nothing to update");
        }
        String title = request.title() == null ? null : validator.title(request.title());
        String description = validator.description(request.description());
        String location = request.location() == null ? null : validator.location(request.location());
        Priority priority = request.priority() == null ? null : validator.priority(request.priority());
        String assignee = request.assignee() == null ? null : validator.assignee(request.assignee());

        if ((priority != null || assignee != null) && actor.role() != Role.MANAGER) {
            throw new ApiException(403, "only a manager can change priority or assignee");
        }
        if (order.getStatus().isClosed()) {
            throw new ApiException(409, "work order is closed");
        }

        List<String> changes = new ArrayList<>();
        if (differs(title, order.getTitle())) {
            changes.add("title: " + order.getTitle() + " -> " + title);
            order.setTitle(title);
        }
        if (differs(description, order.getDescription())) {
            changes.add("description: " + order.getDescription() + " -> " + description);
            order.setDescription(description);
        }
        if (differs(location, order.getLocation())) {
            changes.add("location: " + order.getLocation() + " -> " + location);
            order.setLocation(location);
        }
        if (priority != null && priority != order.getPriority()) {
            changes.add("priority: " + order.getPriority() + " -> " + priority);
            order.setPriority(priority);
        }
        if (differs(assignee, order.getAssignee())) {
            changes.add("assignee: " + Objects.toString(order.getAssignee(), "none") + " -> " + assignee);
            order.setAssignee(assignee);
        }
        for (String change : changes) {
            history.record(order.getId(), "UPDATED", change, actor.user());
        }
        if (!changes.isEmpty()) {
            order.setUpdatedAt(Instant.now());
        }
        return order;
    }

    @Transactional
    public WorkOrder transition(Long id, Transition request, Actor actor) {
        WorkOrder order = require(id);
        Status next = validator.status(request.status());
        String note = validator.note(request.note());
        workflow.check(order, next, actor);

        Instant now = Instant.now();
        order.setStatus(next);
        order.setUpdatedAt(now);
        if (next == Status.DONE) {
            order.setCompletedAt(now);
        }
        String suffix = note.isEmpty() ? "" : " (" + note + ")";
        history.record(order.getId(), "STATUS_CHANGED", order.getStatus() + " -> " + next + suffix, actor.user());
        return order;
    }

    private static boolean differs(String candidate, String current) {
        return candidate != null;
    }
}
