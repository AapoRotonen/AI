package com.supportai.service;

import com.supportai.api.ApiDtos.ServiceStatusView;
import com.supportai.domain.repo.ServiceStatusRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Locale;

@Service
public class ServiceStatusService {
    private final ServiceStatusRepository statuses;
    public ServiceStatusService(ServiceStatusRepository statuses) { this.statuses = statuses; }

    @Transactional(readOnly = true)
    public ServiceStatusView check(String serviceName) {
        if (serviceName == null || serviceName.isBlank() || serviceName.length() > 80) {
            throw new IllegalArgumentException("A service name of 1 to 80 characters is required.");
        }
        String normalized = serviceName.trim().toUpperCase(Locale.ROOT).replace('-', '_').replace(' ', '_');
        return statuses.findById(normalized).map(ServiceStatusView::from)
                .orElseThrow(() -> new ResourceNotFoundException());
    }
}
