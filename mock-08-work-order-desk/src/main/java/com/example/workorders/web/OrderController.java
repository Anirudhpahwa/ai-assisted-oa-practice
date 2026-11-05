package com.example.workorders.web;

import com.example.workorders.common.Actor;
import com.example.workorders.dto.ListQuery;
import com.example.workorders.dto.Requests.AddPart;
import com.example.workorders.dto.Requests.CreateOrder;
import com.example.workorders.dto.Requests.Transition;
import com.example.workorders.dto.Requests.UpdateOrder;
import com.example.workorders.dto.Views.HistoryView;
import com.example.workorders.dto.Views.OrderView;
import com.example.workorders.dto.Views.PageView;
import com.example.workorders.dto.Views.PartView;
import com.example.workorders.dto.Views.SummaryView;
import com.example.workorders.service.HistoryService;
import com.example.workorders.service.OrderService;
import com.example.workorders.service.OrderValidator;
import com.example.workorders.service.PartService;
import com.example.workorders.service.SummaryService;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/orders")
public class OrderController {

    private static final String USER = "X-User";
    private static final String ROLE = "X-Role";

    private final OrderService orders;
    private final OrderValidator validator;
    private final PartService parts;
    private final SummaryService summaries;
    private final HistoryService history;

    public OrderController(OrderService orders, OrderValidator validator, PartService parts,
                           SummaryService summaries, HistoryService history) {
        this.orders = orders;
        this.validator = validator;
        this.parts = parts;
        this.summaries = summaries;
        this.history = history;
    }

    @PostMapping
    public ResponseEntity<OrderView> create(
            @RequestHeader(value = USER, required = false) String user,
            @RequestHeader(value = ROLE, required = false) String role,
            @RequestBody(required = false) CreateOrder body) {
        Actor actor = Actor.from(user, role);
        CreateOrder request = body == null ? new CreateOrder(null, null, null, null) : body;
        return ResponseEntity.status(201).body(OrderView.of(orders.create(request, actor)));
    }

    @GetMapping
    public PageView<OrderView> list(
            @RequestHeader(value = USER, required = false) String user,
            @RequestHeader(value = ROLE, required = false) String role,
            @RequestParam(name = "status", required = false) String status,
            @RequestParam(name = "priority", required = false) String priority,
            @RequestParam(name = "assignee", required = false) String assignee,
            @RequestParam(name = "q", required = false) String q,
            @RequestParam(name = "page", required = false) String page,
            @RequestParam(name = "limit", required = false) String size,
            @RequestParam(name = "sort", required = false) String sort) {
        Actor.from(user, role);
        ListQuery query = validator.list(status, priority, assignee, q, page, size, sort);
        return orders.list(query);
    }

    @GetMapping("/{id}")
    public OrderView show(
            @RequestHeader(value = USER, required = false) String user,
            @RequestHeader(value = ROLE, required = false) String role,
            @PathVariable Long id) {
        Actor.from(user, role);
        return OrderView.of(orders.require(id));
    }

    @PatchMapping("/{id}")
    public OrderView update(
            @RequestHeader(value = USER, required = false) String user,
            @RequestHeader(value = ROLE, required = false) String role,
            @PathVariable Long id,
            @RequestBody(required = false) UpdateOrder body) {
        Actor actor = Actor.from(user, role);
        UpdateOrder request = body == null ? new UpdateOrder(null, null, null, null, null) : body;
        return OrderView.of(orders.update(id, request, actor));
    }

    @PostMapping("/{id}/transition")
    public OrderView transition(
            @RequestHeader(value = USER, required = false) String user,
            @RequestHeader(value = ROLE, required = false) String role,
            @PathVariable Long id,
            @RequestBody(required = false) Transition body) {
        Actor actor = Actor.from(user, role);
        Transition request = body == null ? new Transition(null, null) : body;
        return OrderView.of(orders.transition(id, request, actor));
    }

    @PostMapping("/{id}/parts")
    public ResponseEntity<PartView> addPart(
            @RequestHeader(value = USER, required = false) String user,
            @RequestHeader(value = ROLE, required = false) String role,
            @PathVariable Long id,
            @RequestBody(required = false) AddPart body) {
        Actor actor = Actor.from(user, role);
        AddPart request = body == null ? new AddPart(null, null, null) : body;
        return ResponseEntity.status(201).body(PartView.of(parts.add(id, request, actor)));
    }

    @GetMapping("/{id}/summary")
    public SummaryView summary(
            @RequestHeader(value = USER, required = false) String user,
            @RequestHeader(value = ROLE, required = false) String role,
            @PathVariable Long id) {
        Actor.from(user, role);
        return summaries.summarize(id);
    }

    @GetMapping("/{id}/history")
    public List<HistoryView> history(
            @RequestHeader(value = USER, required = false) String user,
            @RequestHeader(value = ROLE, required = false) String role,
            @PathVariable Long id) {
        Actor.from(user, role);
        orders.require(id);
        return history.forOrder(id).stream().map(HistoryView::of).toList();
    }
}
