package com.example.workorders.model;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;

@Entity
@Table(name = "history_entries")
public class HistoryEntry {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long orderId;
    private String action;
    private String detail;
    private String actor;
    private Instant at;

    public HistoryEntry() {
    }

    public HistoryEntry(Long orderId, String action, String detail, String actor, Instant at) {
        this.orderId = orderId;
        this.action = action;
        this.detail = detail;
        this.actor = actor;
        this.at = at;
    }

    public Long getId() { return id; }
    public Long getOrderId() { return orderId; }
    public String getAction() { return action; }
    public String getDetail() { return detail; }
    public String getActor() { return actor; }
    public Instant getAt() { return at; }
}
