package com.supportai.service;

import com.supportai.api.ApiDtos.TicketView;
import com.supportai.domain.Role;
import com.supportai.domain.TicketPriority;
import com.supportai.domain.TicketStatus;
import com.supportai.domain.entity.AppUser;
import com.supportai.domain.entity.Customer;
import com.supportai.domain.entity.SupportTicket;
import com.supportai.domain.repo.CustomerOrderRepository;
import com.supportai.domain.repo.SupportTicketRepository;
import com.supportai.domain.repo.TicketEventRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.access.AccessDeniedException;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class TicketServiceAuthorizationTest {
    private SupportTicketRepository tickets;
    private CurrentActorService actors;
    private TicketService service;
    private AppUser agent;
    private AppUser other;
    private SupportTicket assigned;
    private SupportTicket restricted;

    @BeforeEach
    void setUp() {
        tickets = mock(SupportTicketRepository.class);
        actors = mock(CurrentActorService.class);
        service = new TicketService(tickets, mock(TicketEventRepository.class), mock(CustomerOrderRepository.class),
                actors, mock(AuditService.class));
        agent = user(1L, "agent@supportai.demo", Role.SUPPORT_AGENT);
        other = user(2L, "other.agent@supportai.demo", Role.SUPPORT_AGENT);
        Customer customer = new Customer(101L, "Alex Example", "alex@example.invalid");
        assigned = new SupportTicket(1001L, customer, "Account access", "Reset did not work.",
                TicketStatus.IN_PROGRESS, TicketPriority.HIGH, agent);
        restricted = new SupportTicket(2002L, customer, "Private case", "Not for this queue.",
                TicketStatus.OPEN, TicketPriority.LOW, other);
    }

    @Test
    void agentCanReadAssignedTicket() {
        when(actors.requireUser()).thenReturn(agent);
        when(tickets.findById(1001L)).thenReturn(Optional.of(assigned));
        assertEquals(1001L, service.getTicket(1001L).id());
    }

    @Test
    void agentCannotDistinguishUnassignedTicketFromUnknownTicket() {
        when(actors.requireUser()).thenReturn(agent);
        when(tickets.findById(2002L)).thenReturn(Optional.of(restricted));
        when(tickets.findById(9999L)).thenReturn(Optional.empty());
        assertThrows(ResourceNotFoundException.class, () -> service.getTicket(2002L));
        assertThrows(ResourceNotFoundException.class, () -> service.getHistory(2002L));
        assertThrows(ResourceNotFoundException.class, () -> service.getCustomerForTicket(2002L));
        assertThrows(ResourceNotFoundException.class, () -> service.getOrdersForTicketCustomer(2002L));
        assertThrows(ResourceNotFoundException.class, () -> service.getTicket(9999L));
    }

    @Test
    void seniorSupportCanReadAnyTicketButAgentQueueRemainsScoped() {
        AppUser senior = user(3L, "senior@supportai.demo", Role.SENIOR_SUPPORT);
        when(actors.requireUser()).thenReturn(senior);
        when(tickets.findById(2002L)).thenReturn(Optional.of(restricted));
        assertEquals(2002L, service.getTicket(2002L).id());

        when(actors.requireUser()).thenReturn(agent);
        when(tickets.findByAssignedUser_IdOrderByUpdatedAtDesc(1L)).thenReturn(List.of(assigned));
        List<TicketView> visible = service.listVisible();
        assertEquals(List.of(1001L), visible.stream().map(TicketView::id).toList());
    }

    private AppUser user(long id, String email, Role role) {
        AppUser user = new AppUser(email, "test-hash", role);
        user.setId(id);
        return user;
    }
}
