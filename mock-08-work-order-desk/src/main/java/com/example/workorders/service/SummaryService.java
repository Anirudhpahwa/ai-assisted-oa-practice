package com.example.workorders.service;

import com.example.workorders.dto.Views.SummaryView;
import com.example.workorders.model.Part;
import com.example.workorders.model.WorkOrder;
import com.example.workorders.repo.PartRepository;
import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class SummaryService {

    private final PartRepository parts;
    private final OrderService orders;

    public SummaryService(PartRepository parts, OrderService orders) {
        this.parts = parts;
        this.orders = orders;
    }

    @Transactional(readOnly = true)
    public SummaryView summarize(Long orderId) {
        WorkOrder order = orders.require(orderId);
        List<Part> used = parts.findByOrderIdOrderByIdAsc(orderId);
        int quantity = used.stream().mapToInt(Part::getQuantity).sum();
        long cost = used.stream().mapToLong(Part::getUnitCostCents).sum();
        return new SummaryView(orderId, order.getStatus().name(), used.size(), quantity, cost);
    }
}
