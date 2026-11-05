package com.example.workorders;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.request;

import com.example.workorders.model.Part;
import com.example.workorders.model.Priority;
import com.example.workorders.model.Status;
import com.example.workorders.model.WorkOrder;
import com.example.workorders.repo.HistoryRepository;
import com.example.workorders.repo.PartRepository;
import com.example.workorders.repo.WorkOrderRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.NullNode;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder;

@SpringBootTest
@AutoConfigureMockMvc
class OrderApiTest {

    private static final Instant T0 = Instant.parse("2027-01-01T10:00:00Z");

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper json;
    @Autowired WorkOrderRepository orders;
    @Autowired PartRepository parts;
    @Autowired HistoryRepository history;

    record Resp(int status, JsonNode body) {
        String text(String field) {
            return body.get(field).asText();
        }
    }

    @BeforeEach
    void clean() {
        history.deleteAll();
        parts.deleteAll();
        orders.deleteAll();
    }

    Resp call(String method, String path, String user, String role, Object body) throws Exception {
        MockHttpServletRequestBuilder req = request(HttpMethod.valueOf(method), path);
        if (user != null) {
            req.header("X-User", user);
        }
        if (role != null) {
            req.header("X-Role", role);
        }
        if (body != null) {
            String content = body instanceof String s ? s : json.writeValueAsString(body);
            req.contentType(MediaType.APPLICATION_JSON).content(content);
        }
        MvcResult result = mvc.perform(req).andReturn();
        String text = result.getResponse().getContentAsString();
        return new Resp(result.getResponse().getStatus(), text.isEmpty() ? NullNode.getInstance() : json.readTree(text));
    }

    Resp as(String user, String role, String method, String path, Object body) throws Exception {
        return call(method, path, user, role, body);
    }

    WorkOrder seed(String title, String description, Priority priority, Status status, String assignee,
                   int minutes) {
        WorkOrder order = new WorkOrder();
        order.setTitle(title);
        order.setDescription(description);
        order.setLocation("Main building");
        order.setPriority(priority);
        order.setStatus(status);
        order.setAssignee(assignee);
        order.setCreatedBy("seed");
        order.setCreatedAt(T0.plusSeconds(60L * minutes));
        order.setUpdatedAt(T0.plusSeconds(60L * minutes));
        return orders.save(order);
    }

    List<String> ids(Resp response) {
        List<String> titles = new ArrayList<>();
        for (JsonNode item : response.body().get("items")) {
            titles.add(item.get("title").asText());
        }
        return titles;
    }

    List<String> details(Resp response) {
        List<String> details = new ArrayList<>();
        for (JsonNode entry : response.body()) {
            details.add(entry.get("action").asText() + " " + entry.get("detail").asText());
        }
        return details;
    }

    @Test
    void createOrder() throws Exception {
        Resp r = call("POST", "/api/orders", null, null, Map.of("title", "Fix pump"));
        assertEquals(401, r.status());
        assertEquals("X-User header required", r.text("error"));

        r = call("POST", "/api/orders", "  ", null, Map.of("title", "Fix pump"));
        assertEquals(401, r.status());

        r = call("POST", "/api/orders", "dana", "ADMIN", Map.of("title", "Fix pump"));
        assertEquals(400, r.status());
        assertEquals("role must be TECHNICIAN or MANAGER", r.text("error"));

        r = call("POST", "/api/orders", "dana", null, Map.of("title", "  Fix pump  "));
        assertEquals(201, r.status());
        assertEquals("Fix pump", r.text("title"));
        assertEquals("", r.text("description"));
        assertEquals("", r.text("location"));
        assertEquals("MEDIUM", r.text("priority"));
        assertEquals("OPEN", r.text("status"));
        assertEquals(NullNode.getInstance(), r.body().get("assignee"));
        assertEquals("dana", r.text("createdBy"));
        long firstId = r.body().get("id").asLong();

        r = call("POST", "/api/orders", "dana", "MANAGER", Map.of(
                "title", "Replace lamp", "description", " Hallway lamp is out ",
                "location", " Floor 2 ", "priority", "urgent"));
        assertEquals(201, r.status());
        assertEquals("Hallway lamp is out", r.text("description"));
        assertEquals("Floor 2", r.text("location"));
        assertEquals("URGENT", r.text("priority"));

        for (String title : List.of("ab", " ab ", "   ", "x".repeat(101))) {
            r = call("POST", "/api/orders", "dana", null, Map.of("title", title));
            assertEquals(400, r.status());
            assertEquals("title must be 3 to 100 characters", r.text("error"));
        }
        r = call("POST", "/api/orders", "dana", null, Map.of("title", "Fix pump", "description", "d".repeat(501)));
        assertEquals(400, r.status());
        assertEquals("description must be at most 500 characters", r.text("error"));
        r = call("POST", "/api/orders", "dana", null, Map.of("title", "Fix pump", "location", "l".repeat(101)));
        assertEquals(400, r.status());
        assertEquals("location must be at most 100 characters", r.text("error"));
        r = call("POST", "/api/orders", "dana", null, Map.of("title", "Fix pump", "priority", "CRITICAL"));
        assertEquals(400, r.status());
        assertEquals("priority must be URGENT, HIGH, MEDIUM or LOW", r.text("error"));

        assertEquals(2, orders.count());
        r = call("GET", "/api/orders/" + firstId + "/history", "dana", null, null);
        assertEquals(200, r.status());
        assertEquals(List.of("CREATED created"), details(r));
        assertEquals("dana", r.body().get(0).get("actor").asText());
    }

    @Test
    void listOrders() throws Exception {
        seed("Replace filter", "Air handler unit", Priority.LOW, Status.OPEN, null, 1);
        seed("Fix boiler leak", "Water on floor near pump", Priority.HIGH, Status.IN_PROGRESS, "ravi", 2);
        seed("Pump noise", "Replace bearing", Priority.URGENT, Status.OPEN, "ravi", 3);
        seed("Paint hallway", "", Priority.LOW, Status.ON_HOLD, null, 4);
        seed("Old request", "Pump removed", Priority.MEDIUM, Status.CANCELLED, null, 5);
        seed("Pump inspection", "Routine", Priority.MEDIUM, Status.DONE, "ravi", 6);
        seed("Light bulb", "Lobby", Priority.MEDIUM, Status.OPEN, null, 7);

        Resp r = call("GET", "/api/orders", "dana", null, null);
        assertEquals(200, r.status());
        assertEquals(List.of("Light bulb", "Pump inspection", "Paint hallway", "Pump noise",
                "Fix boiler leak", "Replace filter"), ids(r));
        assertEquals(6, r.body().get("total").asInt());
        assertEquals(1, r.body().get("page").asInt());
        assertEquals(10, r.body().get("size").asInt());
        assertEquals(1, r.body().get("totalPages").asInt());

        r = call("GET", "/api/orders?q=pump", "dana", null, null);
        assertEquals(List.of("Pump inspection", "Pump noise", "Fix boiler leak"), ids(r));
        r = call("GET", "/api/orders?q=REPLACE", "dana", null, null);
        assertEquals(List.of("Pump noise", "Replace filter"), ids(r));

        r = call("GET", "/api/orders?status=open,On_Hold", "dana", null, null);
        assertEquals(List.of("Light bulb", "Paint hallway", "Pump noise", "Replace filter"), ids(r));
        r = call("GET", "/api/orders?status=cancelled", "dana", null, null);
        assertEquals(List.of("Old request"), ids(r));
        r = call("GET", "/api/orders?status=done,cancelled", "dana", null, null);
        assertEquals(List.of("Pump inspection", "Old request"), ids(r));

        r = call("GET", "/api/orders?priority=low", "dana", null, null);
        assertEquals(List.of("Paint hallway", "Replace filter"), ids(r));
        r = call("GET", "/api/orders?status=open&assignee=ravi", "dana", null, null);
        assertEquals(List.of("Pump noise"), ids(r));
        r = call("GET", "/api/orders?priority=high&q=pump", "dana", null, null);
        assertEquals(List.of("Fix boiler leak"), ids(r));

        r = call("GET", "/api/orders?sort=priority", "dana", null, null);
        assertEquals(List.of("Pump noise", "Fix boiler leak", "Pump inspection", "Light bulb",
                "Replace filter", "Paint hallway"), ids(r));

        r = call("GET", "/api/orders?size=2&page=2", "dana", null, null);
        assertEquals(List.of("Paint hallway", "Pump noise"), ids(r));
        assertEquals(2, r.body().get("page").asInt());
        assertEquals(2, r.body().get("size").asInt());
        assertEquals(6, r.body().get("total").asInt());
        assertEquals(3, r.body().get("totalPages").asInt());
        r = call("GET", "/api/orders?size=4&page=2", "dana", null, null);
        assertEquals(List.of("Fix boiler leak", "Replace filter"), ids(r));
        assertEquals(2, r.body().get("totalPages").asInt());
        r = call("GET", "/api/orders?size=2&page=4", "dana", null, null);
        assertEquals(List.of(), ids(r));
        assertEquals(6, r.body().get("total").asInt());

        r = call("GET", "/api/orders?page=0", "dana", null, null);
        assertEquals(400, r.status());
        assertEquals("page must be a positive integer", r.text("error"));
        r = call("GET", "/api/orders?size=51", "dana", null, null);
        assertEquals(400, r.status());
        assertEquals("size must be an integer from 1 to 50", r.text("error"));
        r = call("GET", "/api/orders?status=open,bogus", "dana", null, null);
        assertEquals(400, r.status());
        assertEquals("status must be a comma-separated list of OPEN, IN_PROGRESS, ON_HOLD, DONE, CANCELLED",
                r.text("error"));
        r = call("GET", "/api/orders?priority=x", "dana", null, null);
        assertEquals(400, r.status());
        r = call("GET", "/api/orders?sort=oldest", "dana", null, null);
        assertEquals(400, r.status());
        assertEquals("sort must be newest or priority", r.text("error"));
    }

    @Test
    void updateOrder() throws Exception {
        WorkOrder order = seed("Fix pump", "Leaks at base", Priority.MEDIUM, Status.OPEN, null, 1);
        order.setLocation("Basement");
        orders.save(order);
        String url = "/api/orders/" + order.getId();

        Resp r = call("PATCH", url, "dana", null, Map.of("title", " Fix pump seal "));
        assertEquals(200, r.status());
        assertEquals("Fix pump seal", r.text("title"));
        assertEquals("Leaks at base", r.text("description"));
        assertEquals("Basement", r.text("location"));
        assertEquals("MEDIUM", r.text("priority"));

        r = call("PATCH", url, "dana", null, Map.of("title", "Fix pump seal", "location", "Boiler room"));
        assertEquals(200, r.status());
        assertEquals("Boiler room", r.text("location"));
        r = call("GET", url + "/history", "dana", null, null);
        assertEquals(List.of("UPDATED title: Fix pump -> Fix pump seal",
                "UPDATED location: Basement -> Boiler room"), details(r));

        r = call("PATCH", url, "dana", null, Map.of("priority", "HIGH"));
        assertEquals(403, r.status());
        assertEquals("only a manager can change priority or assignee", r.text("error"));
        r = call("PATCH", url, "dana", "TECHNICIAN", Map.of("assignee", "ravi"));
        assertEquals(403, r.status());

        r = call("PATCH", url, "kim", "manager", Map.of("priority", "high", "assignee", " ravi "));
        assertEquals(200, r.status());
        assertEquals("HIGH", r.text("priority"));
        assertEquals("ravi", r.text("assignee"));
        r = call("GET", url + "/history", "dana", null, null);
        assertEquals(List.of("UPDATED title: Fix pump -> Fix pump seal",
                "UPDATED location: Basement -> Boiler room",
                "UPDATED priority: MEDIUM -> HIGH",
                "UPDATED assignee: none -> ravi"), details(r));
        assertEquals("kim", r.body().get(3).get("actor").asText());

        r = call("PATCH", url, "dana", null, Map.of());
        assertEquals(400, r.status());
        assertEquals("nothing to update", r.text("error"));
        r = call("PATCH", url, "dana", null, Map.of("title", "ab"));
        assertEquals(400, r.status());
        assertEquals("title must be 3 to 100 characters", r.text("error"));
        r = call("PATCH", url, "kim", "MANAGER", Map.of("assignee", " "));
        assertEquals(400, r.status());
        assertEquals("assignee must be 1 to 50 characters", r.text("error"));

        r = call("PATCH", "/api/orders/999999", "dana", null, Map.of("title", "Whatever"));
        assertEquals(404, r.status());
        assertEquals("work order not found", r.text("error"));

        WorkOrder done = seed("Finished job", "Done long ago", Priority.LOW, Status.DONE, "ravi", 2);
        r = call("PATCH", "/api/orders/" + done.getId(), "dana", null, Map.of("title", "Reopen it"));
        assertEquals(409, r.status());
        assertEquals("work order is closed", r.text("error"));
    }

    @Test
    void transitionOrder() throws Exception {
        WorkOrder order = seed("Replace compressor", "Noisy unit", Priority.HIGH, Status.OPEN, null, 1);
        String base = "/api/orders/" + order.getId();

        Resp r = call("POST", base + "/transition", "ravi", null, Map.of("status", "IN_PROGRESS"));
        assertEquals(409, r.status());
        assertEquals("assignee required", r.text("error"));

        order.setAssignee("ravi");
        orders.save(order);
        r = call("POST", base + "/transition", "ravi", null, Map.of("status", "in_progress", "note", " start now "));
        assertEquals(200, r.status());
        assertEquals("IN_PROGRESS", r.text("status"));

        r = call("POST", base + "/transition", "ravi", null, Map.of("status", "ON_HOLD"));
        assertEquals(200, r.status());
        assertEquals("ON_HOLD", r.text("status"));
        r = call("POST", base + "/transition", "ravi", null, Map.of("status", "OPEN"));
        assertEquals(409, r.status());
        assertEquals("invalid transition", r.text("error"));
        r = call("POST", base + "/transition", "ravi", "TECHNICIAN", Map.of("status", "CANCELLED"));
        assertEquals(403, r.status());
        assertEquals("only a manager can cancel", r.text("error"));

        r = call("POST", base + "/transition", "ravi", null, Map.of("status", "IN_PROGRESS"));
        assertEquals(200, r.status());
        assertEquals("IN_PROGRESS", r.text("status"));

        r = call("POST", base + "/transition", "ravi", null, Map.of("status", "bogus"));
        assertEquals(400, r.status());
        assertEquals("status must be one of OPEN, IN_PROGRESS, ON_HOLD, DONE, CANCELLED", r.text("error"));
        r = call("POST", base + "/transition", "ravi", null, Map.of("status", "DONE", "note", "n".repeat(201)));
        assertEquals(400, r.status());
        assertEquals("note must be at most 200 characters", r.text("error"));

        r = call("POST", base + "/transition", "ravi", null, Map.of("status", "DONE"));
        assertEquals(200, r.status());
        assertEquals("DONE", r.text("status"));
        r = call("POST", base + "/transition", "kim", "MANAGER", Map.of("status", "CANCELLED"));
        assertEquals(409, r.status());
        assertEquals("invalid transition", r.text("error"));
        r = call("POST", base + "/transition", "ravi", null, Map.of("status", "IN_PROGRESS"));
        assertEquals(409, r.status());

        r = call("GET", base + "/history", "ravi", null, null);
        assertEquals(List.of("STATUS_CHANGED OPEN -> IN_PROGRESS (start now)",
                "STATUS_CHANGED IN_PROGRESS -> ON_HOLD",
                "STATUS_CHANGED ON_HOLD -> IN_PROGRESS",
                "STATUS_CHANGED IN_PROGRESS -> DONE"), details(r));
        assertEquals("ravi", r.body().get(0).get("actor").asText());

        WorkOrder other = seed("Cancel me", "Not needed", Priority.LOW, Status.OPEN, null, 2);
        r = call("POST", "/api/orders/" + other.getId() + "/transition", "kim", "MANAGER", Map.of("status", "CANCELLED"));
        assertEquals(200, r.status());
        assertEquals("CANCELLED", r.text("status"));
    }

    @Test
    void addParts() throws Exception {
        WorkOrder waiting = seed("Not started", "Open job", Priority.LOW, Status.OPEN, "ravi", 1);
        Resp r = call("POST", "/api/orders/" + waiting.getId() + "/parts", "ravi", null,
                Map.of("name", "Gasket", "quantity", 1, "unitCostCents", 100));
        assertEquals(409, r.status());
        assertEquals("parts can only be added while in progress", r.text("error"));

        WorkOrder order = seed("Fix valve", "Stuck valve", Priority.HIGH, Status.IN_PROGRESS, "ravi", 2);
        String url = "/api/orders/" + order.getId() + "/parts";

        r = call("POST", url, "ravi", null, Map.of("name", " Gasket ", "quantity", 2, "unitCostCents", 350));
        assertEquals(201, r.status());
        assertEquals("Gasket", r.text("name"));
        assertEquals(2, r.body().get("quantity").asInt());
        assertEquals(350, r.body().get("unitCostCents").asInt());

        r = call("POST", url, "ravi", null, Map.of("name", "gasket", "quantity", 1, "unitCostCents", 100));
        assertEquals(409, r.status());
        assertEquals("part already added", r.text("error"));

        r = call("POST", url, "ravi", null, Map.of("name", " ", "quantity", 1, "unitCostCents", 100));
        assertEquals(400, r.status());
        assertEquals("name must be 1 to 60 characters", r.text("error"));
        for (Object quantity : List.of(0, 101)) {
            r = call("POST", url, "ravi", null, Map.of("name", "Seal", "quantity", quantity, "unitCostCents", 100));
            assertEquals(400, r.status());
            assertEquals("quantity must be an integer from 1 to 100", r.text("error"));
        }
        r = call("POST", url, "ravi", null, "{\"name\":\"Seal\",\"unitCostCents\":100}");
        assertEquals(400, r.status());
        assertEquals("quantity must be an integer from 1 to 100", r.text("error"));
        for (Object cost : List.of(-1, 1000001)) {
            r = call("POST", url, "ravi", null, Map.of("name", "Seal", "quantity", 1, "unitCostCents", cost));
            assertEquals(400, r.status());
            assertEquals("unitCostCents must be an integer from 0 to 1000000", r.text("error"));
        }

        r = call("POST", url, "ravi", null, Map.of("name", "Sealant tape", "quantity", 3, "unitCostCents", 0));
        assertEquals(201, r.status());
        assertEquals(2, parts.count());

        r = call("POST", "/api/orders/999999/parts", "ravi", null,
                Map.of("name", "Seal", "quantity", 1, "unitCostCents", 100));
        assertEquals(404, r.status());

        r = call("GET", "/api/orders/" + order.getId() + "/history", "ravi", null, null);
        assertEquals(List.of("PART_ADDED Gasket x2", "PART_ADDED Sealant tape x3"), details(r));
    }

    @Test
    void orderSummary() throws Exception {
        WorkOrder order = seed("Service boiler", "Yearly service", Priority.MEDIUM, Status.IN_PROGRESS, "ravi", 1);
        parts.save(new Part(order.getId(), "Valve", 2, 1500));
        parts.save(new Part(order.getId(), "Gasket", 4, 250));
        parts.save(new Part(order.getId(), "Oil", 1, 899));

        Resp r = call("GET", "/api/orders/" + order.getId() + "/summary", "dana", null, null);
        assertEquals(200, r.status());
        assertEquals(order.getId().longValue(), r.body().get("orderId").asLong());
        assertEquals("IN_PROGRESS", r.text("status"));
        assertEquals(3, r.body().get("partLines").asInt());
        assertEquals(7, r.body().get("totalQuantity").asInt());
        assertEquals(4899L, r.body().get("totalCostCents").asLong());

        WorkOrder empty = seed("No parts yet", "Nothing used", Priority.LOW, Status.OPEN, null, 2);
        r = call("GET", "/api/orders/" + empty.getId() + "/summary", "dana", null, null);
        assertEquals(0, r.body().get("partLines").asInt());
        assertEquals(0, r.body().get("totalQuantity").asInt());
        assertEquals(0L, r.body().get("totalCostCents").asLong());

        WorkOrder other = seed("Other job", "Different order", Priority.LOW, Status.DONE, "ravi", 3);
        parts.save(new Part(other.getId(), "Belt", 3, 1000));
        r = call("GET", "/api/orders/" + other.getId() + "/summary", "dana", null, null);
        assertEquals(1, r.body().get("partLines").asInt());
        assertEquals(3000L, r.body().get("totalCostCents").asLong());

        r = call("GET", "/api/orders/999999/summary", "dana", null, null);
        assertEquals(404, r.status());
        r = call("GET", "/api/orders/" + order.getId() + "/summary", null, null, null);
        assertEquals(401, r.status());
    }
}
