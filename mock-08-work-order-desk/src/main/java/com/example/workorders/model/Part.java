package com.example.workorders.model;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "parts")
public class Part {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long orderId;
    private String name;
    private int quantity;
    private int unitCostCents;

    public Part() {
    }

    public Part(Long orderId, String name, int quantity, int unitCostCents) {
        this.orderId = orderId;
        this.name = name;
        this.quantity = quantity;
        this.unitCostCents = unitCostCents;
    }

    public Long getId() { return id; }
    public Long getOrderId() { return orderId; }
    public String getName() { return name; }
    public int getQuantity() { return quantity; }
    public int getUnitCostCents() { return unitCostCents; }
}
