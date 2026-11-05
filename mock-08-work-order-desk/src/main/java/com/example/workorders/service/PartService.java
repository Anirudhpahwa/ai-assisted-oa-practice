package com.example.workorders.service;

import com.example.workorders.common.Actor;
import com.example.workorders.common.ApiException;
import com.example.workorders.dto.Requests.AddPart;
import com.example.workorders.model.Part;
import com.example.workorders.model.Status;
import com.example.workorders.model.WorkOrder;
import com.example.workorders.repo.PartRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PartService {

    private final PartRepository parts;
    private final OrderService orders;
    private final OrderValidator validator;
    private final HistoryService history;

    public PartService(PartRepository parts, OrderService orders, OrderValidator validator,
                       HistoryService history) {
        this.parts = parts;
        this.orders = orders;
        this.validator = validator;
        this.history = history;
    }

    @Transactional
    public Part add(Long orderId, AddPart request, Actor actor) {
        WorkOrder order = orders.require(orderId);
        String name = validator.partName(request.name());
        int quantity = validator.quantity(request.quantity());
        int unitCost = validator.unitCostCents(request.unitCostCents());
        if (order.getStatus() != Status.IN_PROGRESS) {
            throw new ApiException(409, "parts can only be added while in progress");
        }
        if (parts.existsByOrderIdAndName(orderId, name)) {
            throw new ApiException(409, "part already added");
        }
        Part part = parts.save(new Part(orderId, name, quantity, unitCost));
        history.record(orderId, "PART_ADDED", name + " x" + quantity, actor.user());
        return part;
    }
}
