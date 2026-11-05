package com.example.workorders.common;

import com.example.workorders.model.Role;

/** The person making a request, taken from the X-User and X-Role headers. */
public record Actor(String user, Role role) {

    public static Actor from(String userHeader, String roleHeader) {
        String user = userHeader == null ? "" : userHeader.trim();
        if (user.isEmpty()) {
            throw new ApiException(401, "X-User header required");
        }
        Role role = Role.TECHNICIAN;
        if (roleHeader != null && !roleHeader.isBlank()) {
            role = Role.parse(roleHeader)
                    .orElseThrow(() -> new ApiException(400, "role must be TECHNICIAN or MANAGER"));
        }
        return new Actor(user, role);
    }
}
