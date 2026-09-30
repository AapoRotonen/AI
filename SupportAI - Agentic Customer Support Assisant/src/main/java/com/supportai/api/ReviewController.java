package com.supportai.api;

import com.supportai.api.ApiDtos.ReviewDecision;
import com.supportai.api.ApiDtos.ReviewView;
import com.supportai.service.HumanReviewService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Size;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/reviews")
@Validated
public class ReviewController {
    private final HumanReviewService reviews;
    public ReviewController(HumanReviewService reviews) { this.reviews = reviews; }

    @GetMapping public List<ReviewView> list() { return reviews.listVisible(); }
    @GetMapping("/{id}") public ReviewView get(@PathVariable long id) { return reviews.get(id); }

    @PostMapping("/{id}/approve")
    @PreAuthorize("hasAnyRole('SENIOR_SUPPORT', 'ADMIN')")
    public ReviewView approve(@PathVariable long id, @Valid @RequestBody(required = false) DecisionPayload payload) {
        return reviews.approve(id, payload == null ? null : payload.note());
    }

    @PostMapping("/{id}/reject")
    @PreAuthorize("hasAnyRole('SENIOR_SUPPORT', 'ADMIN')")
    public ReviewView reject(@PathVariable long id, @Valid @RequestBody(required = false) DecisionPayload payload) {
        return reviews.reject(id, payload == null ? null : payload.note());
    }

    public record DecisionPayload(@Size(max = 1000) String note) { }
}
