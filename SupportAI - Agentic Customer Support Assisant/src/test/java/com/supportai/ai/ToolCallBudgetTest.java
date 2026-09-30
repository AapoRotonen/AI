package com.supportai.ai;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertThrows;

class ToolCallBudgetTest {
    @Test
    void rejectsTheNinthToolCallInOneAssistantRequest() {
        ToolCallBudget budget = new ToolCallBudget();
        budget.start();
        try {
            for (int i = 0; i < ToolCallBudget.MAX_TOOL_CALLS_PER_REQUEST; i++) budget.consume();
            assertThrows(AgentIterationLimitException.class, budget::consume);
        } finally {
            budget.clear();
        }
    }
}
