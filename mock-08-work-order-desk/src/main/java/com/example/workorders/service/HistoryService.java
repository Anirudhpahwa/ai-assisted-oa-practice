package com.example.workorders.service;

import com.example.workorders.model.HistoryEntry;
import com.example.workorders.repo.HistoryRepository;
import java.time.Instant;
import java.util.List;
import org.springframework.stereotype.Service;

@Service
public class HistoryService {

    private final HistoryRepository history;

    public HistoryService(HistoryRepository history) {
        this.history = history;
    }

    public void record(Long orderId, String action, String detail, String actor) {
        history.save(new HistoryEntry(orderId, action, detail, actor, Instant.now()));
    }

    public List<HistoryEntry> forOrder(Long orderId) {
        return history.findByOrderIdOrderByIdAsc(orderId);
    }
}
