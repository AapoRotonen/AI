package com.supportai.domain.entity;

import com.supportai.domain.ReviewStatus;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;

@Entity
@Table(name = "human_review")
@Getter
@Setter
@NoArgsConstructor
public class HumanReview {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "ticket_id", nullable = false)
    private SupportTicket ticket;
    @Column(name = "proposed_action", nullable = false, length = 48)
    private String proposedAction;
    @Column(nullable = false, length = 1000)
    private String reason;
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 24)
    private ReviewStatus status;
    @Column(name = "created_by", nullable = false)
    private String createdBy;
    @Column(name = "created_at", nullable = false)
    private Instant createdAt;
    @Column(name = "reviewed_at")
    private Instant reviewedAt;
    @Column(name = "reviewed_by")
    private String reviewedBy;
    @Column(name = "review_note", length = 1000)
    private String reviewNote;

    @PrePersist
    void onCreate() { if (createdAt == null) createdAt = Instant.now(); }

    public HumanReview(SupportTicket ticket, String proposedAction, String reason, String createdBy) {
        this.ticket = ticket;
        this.proposedAction = proposedAction;
        this.reason = reason;
        this.createdBy = createdBy;
        this.status = ReviewStatus.PENDING;
    }
}
