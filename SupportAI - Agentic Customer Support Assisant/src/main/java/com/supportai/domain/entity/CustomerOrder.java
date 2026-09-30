package com.supportai.domain.entity;

import com.supportai.domain.OrderStatus;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;
import java.time.LocalDate;

@Entity
@Table(name = "customer_order")
@Getter
@Setter
@NoArgsConstructor
public class CustomerOrder {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "customer_id", nullable = false)
    private Customer customer;
    @Column(name = "order_number", nullable = false, unique = true, length = 64)
    private String orderNumber;
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private OrderStatus status;
    @Column(name = "tracking_number", length = 64)
    private String trackingNumber;
    @Column(name = "created_at", nullable = false)
    private Instant createdAt;
    @Column(name = "estimated_delivery_date", nullable = false)
    private LocalDate estimatedDeliveryDate;

    public CustomerOrder(Customer customer, String orderNumber, OrderStatus status, String trackingNumber,
                         Instant createdAt, LocalDate estimatedDeliveryDate) {
        this.customer = customer;
        this.orderNumber = orderNumber;
        this.status = status;
        this.trackingNumber = trackingNumber;
        this.createdAt = createdAt;
        this.estimatedDeliveryDate = estimatedDeliveryDate;
    }
}
