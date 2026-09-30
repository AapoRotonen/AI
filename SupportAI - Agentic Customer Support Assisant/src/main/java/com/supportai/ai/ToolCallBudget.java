package com.supportai.ai;

import org.springframework.stereotype.Component;

@Component
public class ToolCallBudget {
    public static final int MAX_TOOL_CALLS_PER_REQUEST = 8;
    private final ThreadLocal<Integer> calls = new ThreadLocal<>();

    public void start() { calls.set(0); }

    public void consume() {
        Integer count = calls.get();
        if (count == null) return;
        if (count >= MAX_TOOL_CALLS_PER_REQUEST) throw new AgentIterationLimitException();
        calls.set(count + 1);
    }

    public void clear() { calls.remove(); }
}
