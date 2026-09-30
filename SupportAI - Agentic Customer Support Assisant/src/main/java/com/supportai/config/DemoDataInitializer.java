package com.supportai.config;

import com.supportai.domain.*;
import com.supportai.domain.entity.*;
import com.supportai.domain.repo.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

import java.time.Instant;
import java.time.LocalDate;

@Configuration
public class DemoDataInitializer {
    @Bean
    CommandLineRunner seedDemoData(AppUserRepository users, CustomerRepository customers, SupportTicketRepository tickets,
                                   TicketEventRepository events, CustomerOrderRepository orders,
                                   ServiceStatusRepository services, PasswordEncoder encoder,
                                   PlatformTransactionManager transactionManager,
                                   @Value("${DEMO_AGENT_PASSWORD:AgentDemo123!}") String agentPassword,
                                   @Value("${DEMO_SENIOR_PASSWORD:SeniorDemo123!}") String seniorPassword,
                                   @Value("${DEMO_OTHER_PASSWORD:OtherDemo123!}") String otherPassword) {
        return args -> new TransactionTemplate(transactionManager).executeWithoutResult(transaction -> {
            AppUser agent = user(users, encoder, "agent@supportai.demo", agentPassword, Role.SUPPORT_AGENT);
            AppUser senior = user(users, encoder, "senior@supportai.demo", seniorPassword, Role.SENIOR_SUPPORT);
            AppUser other = user(users, encoder, "other.agent@supportai.demo", otherPassword, Role.SUPPORT_AGENT);

            Customer account = customer(customers, 101L, "Alex Example", "alex@example.invalid");
            Customer delivery = customer(customers, 102L, "Morgan Sample", "morgan@example.invalid");
            Customer outage = customer(customers, 103L, "Jamie Fiction", "jamie@example.invalid");
            Customer restricted = customer(customers, 104L, "Taylor Demo", "taylor@example.invalid");

            SupportTicket t1001 = ticket(tickets, 1001L, account, "Cannot access account",
                    "Customer reset their password but still cannot sign in.", TicketStatus.IN_PROGRESS, TicketPriority.HIGH, agent);
            SupportTicket t1002 = ticket(tickets, 1002L, delivery, "Order has not arrived",
                    "Customer reports that the parcel has not arrived by the promised date.", TicketStatus.OPEN, TicketPriority.MEDIUM, agent);
            ticket(tickets, 1003L, outage, "Service access problem",
                    "Customer cannot reach the authentication service.", TicketStatus.OPEN, TicketPriority.HIGH, agent);
            ticket(tickets, 2002L, restricted, "Billing question",
                    "Customer asks about a recent invoice.", TicketStatus.OPEN, TicketPriority.LOW, other);

            if (!orders.existsByOrderNumber("ORD-1002-A")) {
                orders.save(new CustomerOrder(delivery, "ORD-1002-A", OrderStatus.DELAYED, "TRK-EXAMPLE-1002",
                        Instant.now().minusSeconds(6 * 86400L), LocalDate.now().minusDays(2)));
            }
            if (!events.existsByTicket_IdAndEventType(1001L, "CUSTOMER_REPORTED")) {
                events.save(new TicketEvent(t1001, "CUSTOMER_REPORTED", "Customer reported a login problem.", "customer"));
                events.save(new TicketEvent(t1001, "PASSWORD_RESET", "Customer completed a password reset; access issue continued.", "support-system"));
                events.save(new TicketEvent(t1001, "ASSIGNED", "Ticket assigned to support for investigation.", agent.getEmail()));
            }
            if (!events.existsByTicket_IdAndEventType(1002L, "CUSTOMER_REPORTED")) {
                events.save(new TicketEvent(t1002, "CUSTOMER_REPORTED", "Customer reports that the expected delivery date passed.", "customer"));
                events.save(new TicketEvent(t1002, "CARRIER_UPDATE", "Carrier tracking shows a regional delivery delay.", "support-system"));
            }
            if (!events.existsByTicket_IdAndEventType(1003L, "CUSTOMER_REPORTED")) {
                events.save(new TicketEvent(tickets.findById(1003L).orElseThrow(), "CUSTOMER_REPORTED", "Customer cannot reach the authentication service.", "customer"));
            }

            service(services, "AUTHENTICATION_SERVICE", ServiceHealth.DEGRADED,
                    "Elevated sign-in failures are being investigated. Check the internal status before troubleshooting account credentials.");
            service(services, "CHECKOUT_SERVICE", ServiceHealth.OPERATIONAL, "Checkout is operating normally.");
            service(services, "ORDER_TRACKING", ServiceHealth.OPERATIONAL, "Order tracking is operating normally.");
        });
    }

    private AppUser user(AppUserRepository repository, PasswordEncoder encoder, String email, String password, Role role) {
        return repository.findByEmailIgnoreCase(email).orElseGet(() -> repository.save(new AppUser(email, encoder.encode(password), role)));
    }

    private Customer customer(CustomerRepository repository, long id, String name, String email) {
        return repository.findById(id).orElseGet(() -> repository.save(new Customer(id, name, email)));
    }

    private SupportTicket ticket(SupportTicketRepository repository, long id, Customer customer, String title,
                                 String description, TicketStatus status, TicketPriority priority, AppUser assignee) {
        return repository.findById(id).orElseGet(() -> repository.save(new SupportTicket(id, customer, title, description, status, priority, assignee)));
    }

    private void service(ServiceStatusRepository repository, String name, ServiceHealth status, String message) {
        if (!repository.existsById(name)) repository.save(new ServiceStatus(name, status, message));
    }
}
