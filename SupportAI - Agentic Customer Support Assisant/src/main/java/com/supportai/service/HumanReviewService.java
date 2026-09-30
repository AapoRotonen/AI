package com.supportai.service;

import com.supportai.api.ApiDtos.ReviewView;
import com.supportai.domain.Role;
import com.supportai.domain.ReviewStatus;
import com.supportai.domain.entity.AppUser;
import com.supportai.domain.entity.HumanReview;
import com.supportai.domain.entity.SupportTicket;
import com.supportai.domain.repo.HumanReviewRepository;
import com.supportai.domain.repo.SupportTicketRepository;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;

@Service
public class HumanReviewService {
    private final HumanReviewRepository reviews;
    private final SupportTicketRepository tickets;
    private final TicketService ticketService;
    private final CurrentActorService currentActor;
    private final ActionPolicy actionPolicy;
    private final AuditService audit;

    public HumanReviewService(HumanReviewRepository reviews, SupportTicketRepository tickets, TicketService ticketService,
                              CurrentActorService currentActor, ActionPolicy actionPolicy, AuditService audit) {
        this.reviews = reviews;
        this.tickets = tickets;
        this.ticketService = ticketService;
        this.currentActor = currentActor;
        this.actionPolicy = actionPolicy;
        this.audit = audit;
    }

    @Transactional
    public ReviewView propose(long ticketId, String requestedAction, String reason) {
        String action = actionPolicy.requireSupportedAction(requestedAction);
        if (reason == null || reason.isBlank() || reason.length() > 1000) {
            throw new IllegalArgumentException("A reason of 1 to 1000 characters is required.");
        }
        AppUser actor = currentActor.requireUser();
        SupportTicket ticket = ticketService.requireAuthorizedTicket(ticketId);
        if (reviews.existsByTicket_IdAndProposedActionAndStatus(ticketId, action, ReviewStatus.PENDING)) {
            throw new IllegalStateException("A matching action is already pending human review.");
        }
        HumanReview review = reviews.save(new HumanReview(ticket, action, reason.trim(), actor.getEmail()));
        audit.record(actor.getEmail(), "ACTION_PROPOSED", "TICKET", ticketId, "PENDING_REVIEW");
        audit.record(actor.getEmail(), "HUMAN_REVIEW_CREATED", "REVIEW", review.getId(), "PENDING");
        return ReviewView.from(review);
    }

    @Transactional(readOnly = true)
    public List<ReviewView> listVisible() {
        AppUser actor = currentActor.requireUser();
        List<HumanReview> visible = actor.getRole() == Role.SUPPORT_AGENT
                ? reviews.findByCreatedByOrderByCreatedAtDesc(actor.getEmail())
                : reviews.findAllByOrderByCreatedAtDesc();
        return visible.stream().map(ReviewView::from).toList();
    }

    @Transactional(readOnly = true)
    public ReviewView get(long id) {
        HumanReview review = reviews.findById(id).orElseThrow(ResourceNotFoundException::new);
        AppUser actor = currentActor.requireUser();
        if (actor.getRole() == Role.SUPPORT_AGENT && !actor.getEmail().equals(review.getCreatedBy())) {
            throw new ResourceNotFoundException();
        }
        return ReviewView.from(review);
    }

    @Transactional
    public ReviewView approve(long id, String note) {
        AppUser reviewer = requireReviewer();
        HumanReview review = requirePending(id);
        if (review.getCreatedBy().equalsIgnoreCase(reviewer.getEmail())) {
            throw new AccessDeniedException("A reviewer cannot approve their own proposal.");
        }
        review.setStatus(ReviewStatus.APPROVED);
        review.setReviewedAt(Instant.now());
        review.setReviewedBy(reviewer.getEmail());
        review.setReviewNote(safeNote(note));
        if ("CLOSE_TICKET".equals(review.getProposedAction())) {
            SupportTicket ticket = tickets.findById(review.getTicket().getId()).orElseThrow(ResourceNotFoundException::new);
            ticketService.closeTicketAfterApproval(ticket, reviewer.getEmail(), review.getReason());
        } else {
            throw new IllegalStateException("The approved action is no longer supported.");
        }
        reviews.save(review);
        audit.record(reviewer.getEmail(), "ACTION_APPROVED", "REVIEW", id, "SUCCESS");
        return ReviewView.from(review);
    }

    @Transactional
    public ReviewView reject(long id, String note) {
        AppUser reviewer = requireReviewer();
        HumanReview review = requirePending(id);
        if (review.getCreatedBy().equalsIgnoreCase(reviewer.getEmail())) {
            throw new AccessDeniedException("A reviewer cannot reject their own proposal.");
        }
        review.setStatus(ReviewStatus.REJECTED);
        review.setReviewedAt(Instant.now());
        review.setReviewedBy(reviewer.getEmail());
        review.setReviewNote(safeNote(note));
        reviews.save(review);
        audit.record(reviewer.getEmail(), "ACTION_REJECTED", "REVIEW", id, "SUCCESS");
        return ReviewView.from(review);
    }

    private HumanReview requirePending(long id) {
        HumanReview review = reviews.findById(id).orElseThrow(ResourceNotFoundException::new);
        if (review.getStatus() != ReviewStatus.PENDING) throw new IllegalStateException("Review is already decided.");
        return review;
    }

    private AppUser requireReviewer() {
        AppUser actor = currentActor.requireUser();
        if (actor.getRole() != Role.SENIOR_SUPPORT && actor.getRole() != Role.ADMIN) {
            throw new AccessDeniedException("Senior support authorization is required.");
        }
        return actor;
    }

    private String safeNote(String note) {
        if (note == null) return null;
        if (note.length() > 1000) throw new IllegalArgumentException("Review note must not exceed 1000 characters.");
        return note.isBlank() ? null : note.trim();
    }
}
