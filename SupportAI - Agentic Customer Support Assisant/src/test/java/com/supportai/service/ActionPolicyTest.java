package com.supportai.service;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class ActionPolicyTest {
    private final ActionPolicy policy = new ActionPolicy();

    @Test
    void onlySupportedStateChangeCanBeRequested() {
        assertEquals("CLOSE_TICKET", policy.requireSupportedAction("close_ticket"));
        assertThrows(IllegalArgumentException.class, () -> policy.requireSupportedAction("REFUND_ORDER"));
        assertThrows(IllegalArgumentException.class, () -> policy.requireSupportedAction("EXECUTE_SQL"));
    }
}
