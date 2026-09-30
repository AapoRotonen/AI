package com.supportai.domain.repo;

import com.supportai.domain.entity.TicketEvent;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface TicketEventRepository extends JpaRepository<TicketEvent, Long> {
    List<TicketEvent> findByTicket_IdOrderByCreatedAtAsc(Long ticketId);
    boolean existsByTicket_IdAndEventType(Long ticketId, String eventType);
}
