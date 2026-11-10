package com.example.roombooking.model;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "rooms")
public class Room {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;
    private int capacity;
    private int hourlyRateCents;
    private boolean active;

    public Room() {
    }

    public Room(String name, int capacity, int hourlyRateCents, boolean active) {
        this.name = name;
        this.capacity = capacity;
        this.hourlyRateCents = hourlyRateCents;
        this.active = active;
    }

    public Long getId() { return id; }
    public String getName() { return name; }
    public int getCapacity() { return capacity; }
    public int getHourlyRateCents() { return hourlyRateCents; }
    public boolean isActive() { return active; }
}
