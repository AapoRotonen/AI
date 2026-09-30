package com.supportai.api;

import com.supportai.api.ApiDtos.*;
import com.supportai.service.TicketService;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/tickets")
public class TicketController {
    private final TicketService tickets;
    public TicketController(TicketService tickets) { this.tickets = tickets; }

    @GetMapping public List<TicketView> list() { return tickets.listVisible(); }
    @GetMapping("/{id}") public TicketView get(@PathVariable long id) { return tickets.getTicket(id); }
    @GetMapping("/{id}/history") public List<TicketEventView> history(@PathVariable long id) { return tickets.getHistory(id); }
    @GetMapping("/{id}/customer") public CustomerView customer(@PathVariable long id) { return tickets.getCustomerForTicket(id); }
    @GetMapping("/{id}/orders") public List<OrderView> orders(@PathVariable long id) { return tickets.getOrdersForTicketCustomer(id); }
}
