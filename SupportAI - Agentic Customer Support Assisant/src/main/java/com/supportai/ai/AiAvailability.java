package com.supportai.ai;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class AiAvailability {
    private static final String OFFLINE_SENTINEL = "supportai-disabled";
    private final boolean enabled;

    public AiAvailability(@Value("${supportai.ai.api-key:supportai-disabled}") String apiKey) {
        this.enabled = apiKey != null && !apiKey.isBlank() && !OFFLINE_SENTINEL.equalsIgnoreCase(apiKey.trim());
    }

    public boolean enabled() { return enabled; }
}
