package com.supportai.ai;

public class AgentIterationLimitException extends RuntimeException {
    public AgentIterationLimitException() { super("The assistant reached its maximum tool-call budget."); }
}
