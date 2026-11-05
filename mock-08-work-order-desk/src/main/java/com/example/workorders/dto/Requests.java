package com.example.workorders.dto;

public final class Requests {

    private Requests() {
    }

    public record CreateOrder(String title, String description, String location, String priority) {
    }

    public record UpdateOrder(String title, String description, String location, String priority,
                              String assignee) {
    }

    public record Transition(String status, String note) {
    }

    public record AddPart(String name, Integer quantity, Integer unitCostCents) {
    }
}
