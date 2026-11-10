package com.example.roombooking.common;

import com.example.roombooking.model.Role;

/** The person making a request, taken from the X-User and X-Role headers. */
public record Actor(String user, Role role) {

    public static Actor from(String userHeader, String roleHeader) {
        String user = userHeader == null ? "" : userHeader.trim();
        if (user.isEmpty()) {
            throw new ApiException(401, "X-User header required");
        }
        Role role = Role.USER;
        if (roleHeader != null && !roleHeader.isBlank()) {
            role = Role.parse(roleHeader)
                    .orElseThrow(() -> new ApiException(400, "role must be USER or MANAGER"));
        }
        return new Actor(user, role);
    }
}
