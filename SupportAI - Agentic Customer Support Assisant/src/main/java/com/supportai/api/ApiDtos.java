package com.supportai.api;

import com.supportai.domain.*;
import com.supportai.domain.entity.*;

import java.time.Instant;
import java.time.LocalDate;
import java.util.List;

public final class ApiDtos {
    private ApiDtos() { }

    public record LoginRequest(String email, String password) { }
    public record LoginResponse(String accessToken, String tokenType, Instant expiresAt, String email, Role role) { }
    public record TicketView(long id, String title, String description, TicketStatus status, TicketPriority priority,
                             long customerId, String customerName, Instant createdAt, Instant updatedAt) {
        public static TicketView from(SupportTicket ticket) {
            return new TicketView(ticket.getId(), ticket.getTitle(), ticket.getDescription(), ticket.getStatus(),
                    ticket.getPriority(), ticket.getCustomer().getId(), ticket.getCustomer().getName(),
                    ticket.getCreatedAt(), ticket.getUpdatedAt());
        }
    }
    public record CustomerView(long id, String name) {
        public static CustomerView from(Customer customer) {
            return new CustomerView(customer.getId(), customer.getName());
        }
    }
    public record TicketEventView(long id, String eventType, String description, Instant createdAt) {
        public static TicketEventView from(TicketEvent event) {
            return new TicketEventView(event.getId(), event.getEventType(), event.getDescription(), event.getCreatedAt());
        }
    }
    public record OrderView(String orderNumber, OrderStatus status, String trackingNumber, Instant createdAt,
                            LocalDate estimatedDeliveryDate) {
        public static OrderView from(CustomerOrder order) {
            return new OrderView(order.getOrderNumber(), order.getStatus(), order.getTrackingNumber(),
                    order.getCreatedAt(), order.getEstimatedDeliveryDate());
        }
    }
    public record ServiceStatusView(String serviceName, ServiceHealth status, String publicMessage, Instant checkedAt) {
        public static ServiceStatusView from(ServiceStatus service) {
            return new ServiceStatusView(service.getServiceName(), service.getStatus(), service.getPublicMessage(), service.getCheckedAt());
        }
    }
    public record ReviewView(long id, long ticketId, String proposedAction, String reason, ReviewStatus status,
                             String createdBy, Instant createdAt, Instant reviewedAt, String reviewedBy, String reviewNote) {
        public static ReviewView from(HumanReview review) {
            return new ReviewView(review.getId(), review.getTicket().getId(), review.getProposedAction(), review.getReason(),
                    review.getStatus(), review.getCreatedBy(), review.getCreatedAt(), review.getReviewedAt(),
                    review.getReviewedBy(), review.getReviewNote());
        }
    }
    public record AssistantRequest(String message) { }
    public record AssistantResponse(String answer, boolean aiEnabled, List<String> availableTools) { }
    public record ReviewDecision(String note) { }
    public record ErrorResponse(Instant timestamp, int status, String code, String message, String requestId) { }

    public record TicketToolResult(TicketView ticket) { }
    public record CustomerToolResult(CustomerView customer) { }
    public record HistoryToolResult(List<TicketEventView> events) { }
    public record OrdersToolResult(List<OrderView> orders) { }
    public record KnowledgeSource(String documentId, String title, String category) { }
    public record KnowledgeToolResult(String answer, List<KnowledgeSource> sources) { }
    public record ProposedActionResult(long reviewId, long ticketId, String action, ReviewStatus status, String message) { }
}
