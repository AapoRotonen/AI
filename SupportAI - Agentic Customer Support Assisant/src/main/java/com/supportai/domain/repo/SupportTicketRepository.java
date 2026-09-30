package com.supportai.domain.repo;

import com.supportai.domain.entity.SupportTicket;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface SupportTicketRepository extends JpaRepository<SupportTicket, Long> {
    List<SupportTicket> findAllByOrderByUpdatedAtDesc();
    List<SupportTicket> findByAssignedUser_IdOrderByUpdatedAtDesc(Long assignedUserId);
}
