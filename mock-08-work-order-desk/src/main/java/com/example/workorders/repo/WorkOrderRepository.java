package com.example.workorders.repo;

import com.example.workorders.model.WorkOrder;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

public interface WorkOrderRepository
        extends JpaRepository<WorkOrder, Long>, JpaSpecificationExecutor<WorkOrder> {
}
