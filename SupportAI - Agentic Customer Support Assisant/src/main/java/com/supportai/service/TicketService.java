package com.supportai.service;

import com.supportai.api.ApiDtos.*;
import com.supportai.domain.Role;
import com.supportai.domain.TicketStatus;
import com.supportai.domain.entity.*;
import com.supportai.domain.repo.*;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;

@Service
public class TicketService {
    private final SupportTicketRepository tickets;
    private final TicketEventRepository history;
    private final CustomerOrderRepository orders;
    private final CurrentActorService currentActor;
    private final AuditService audit;

    public TicketService(SupportTicketRepository tickets, TicketEventRepository history, CustomerOrderRepository orders,
                        CurrentActorService currentActor, AuditService audit) {
        this.tickets = tickets;
        this.history = history;
        this.orders = orders;
        this.currentActor = currentActor;
        this.audit = audit;
    }

    @Transactional(readOnly = true)
    public List<TicketView> listVisible() {
        AppUser actor = currentActor.requireUser();
        List<SupportTicket> result = actor.getRole() == Role.SUPPORT_AGENT
                ? tickets.findByAssignedUser_IdOrderByUpdatedAtDesc(actor.getId())
                : tickets.findAllByOrderByUpdatedAtDesc();
        return result.stream().map(TicketView::from).toList();
    }

    @Transactional(readOnly = true)
    public TicketView getTicket(long id) { return TicketView.from(requireAuthorizedTicket(id)); }

    @Transactional(readOnly = true)
    public List<TicketEventView> getHistory(long id) {
        requireAuthorizedTicket(id);
        return history.findByTicket_IdOrderByCreatedAtAsc(id).stream().map(TicketEventView::from).toList();
    }

    @Transactional(readOnly = true)
    public CustomerView getCustomerForTicket(long id) {
        return CustomerView.from(requireAuthorizedTicket(id).getCustomer());
    }

    @Transactional(readOnly = true)
    public List<OrderView> getOrdersForTicketCustomer(long id) {
        SupportTicket ticket = requireAuthorizedTicket(id);
        return orders.findByCustomer_IdOrderByCreatedAtDesc(ticket.getCustomer().getId())
                .stream().map(OrderView::from).toList();
    }

    @Transactional
    SupportTicket closeTicketAfterApproval(SupportTicket ticket, String actor, String reason) {
        if (ticket.getStatus() == TicketStatus.CLOSED) return ticket;
        ticket.setStatus(TicketStatus.CLOSED);
        ticket.setUpdatedAt(Instant.now());
        SupportTicket saved = tickets.save(ticket);
        history.save(new TicketEvent(saved, "STATUS_CHANGED", "Ticket closed after approved human review.", actor));
        audit.record(actor, "TICKET_STATUS_CHANGED", "TICKET", ticket.getId(), "SUCCESS");
        return saved;
    }

    @Transactional(readOnly = true)
    public SupportTicket requireAuthorizedTicket(long id) {
        AppUser actor = currentActor.requireUser();
        SupportTicket ticket = tickets.findById(id).orElseThrow(ResourceNotFoundException::new);
        if (actor.getRole() == Role.SUPPORT_AGENT && !ticket.getAssignedUser().getId().equals(actor.getId())) {
            audit.record(actor.getEmail(), "TICKET_ACCESS_DENIED", "TICKET", id, "DENIED");
            // Hide whether an out-of-scope ticket exists: the response is the same as an unknown ID.
            throw new ResourceNotFoundException();
        }
        return ticket;
    }
}
