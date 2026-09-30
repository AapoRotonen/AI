package com.supportai.api;

import com.supportai.ai.AssistantService;
import com.supportai.api.ApiDtos.AssistantRequest;
import com.supportai.api.ApiDtos.AssistantResponse;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/assistant")
@Validated
public class AssistantController {
    private final AssistantService assistant;
    public AssistantController(AssistantService assistant) { this.assistant = assistant; }

    @PostMapping("/chat")
    public AssistantResponse chat(@Valid @RequestBody ChatRequest request) { return assistant.chat(request.message()); }

    public record ChatRequest(@NotBlank @Size(max = 1200) String message) { }
}
