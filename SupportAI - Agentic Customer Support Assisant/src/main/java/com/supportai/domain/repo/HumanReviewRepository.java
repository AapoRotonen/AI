package com.supportai.domain.repo;

import com.supportai.domain.ReviewStatus;
import com.supportai.domain.entity.HumanReview;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface HumanReviewRepository extends JpaRepository<HumanReview, Long> {
    List<HumanReview> findAllByOrderByCreatedAtDesc();
    List<HumanReview> findByStatusOrderByCreatedAtDesc(ReviewStatus status);
    List<HumanReview> findByCreatedByOrderByCreatedAtDesc(String createdBy);
    boolean existsByTicket_IdAndProposedActionAndStatus(Long ticketId, String proposedAction, ReviewStatus status);
}
