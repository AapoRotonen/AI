package com.supportai.service;

import org.springframework.stereotype.Component;

import java.util.Locale;

@Component
public class ActionPolicy {
    public String requireSupportedAction(String action) {
        if (action == null || !"CLOSE_TICKET".equals(action.trim().toUpperCase(Locale.ROOT))) {
            throw new IllegalArgumentException("Only CLOSE_TICKET can be proposed in this PoC.");
        }
        return "CLOSE_TICKET";
    }
}
