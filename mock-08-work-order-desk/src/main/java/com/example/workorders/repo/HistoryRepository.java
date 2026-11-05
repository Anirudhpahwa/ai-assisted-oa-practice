package com.example.workorders.repo;

import com.example.workorders.model.HistoryEntry;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface HistoryRepository extends JpaRepository<HistoryEntry, Long> {

    List<HistoryEntry> findByOrderIdOrderByIdAsc(Long orderId);
}
