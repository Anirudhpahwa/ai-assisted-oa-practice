package com.example.workorders.repo;

import com.example.workorders.model.Part;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PartRepository extends JpaRepository<Part, Long> {

    List<Part> findByOrderIdOrderByIdAsc(Long orderId);

    boolean existsByOrderIdAndName(Long orderId, String name);
}
