package com.supportai.domain.entity;

import com.supportai.domain.ServiceHealth;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.Instant;

@Entity
@Table(name = "service_status")
@Getter
@Setter
@NoArgsConstructor
public class ServiceStatus {
    @Id
    @Column(name = "service_name", length = 80)
    private String serviceName;
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private ServiceHealth status;
    @Column(name = "public_message", nullable = false, length = 500)
    private String publicMessage;
    @Column(name = "checked_at", nullable = false)
    private Instant checkedAt;

    public ServiceStatus(String serviceName, ServiceHealth status, String publicMessage) {
        this.serviceName = serviceName;
        this.status = status;
        this.publicMessage = publicMessage;
        this.checkedAt = Instant.now();
    }
}
