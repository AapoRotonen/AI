package com.supportai.service;

import com.supportai.domain.entity.AuditEvent;
import com.supportai.domain.repo.AuditEventRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuditService {
    private final AuditEventRepository events;

    public AuditService(AuditEventRepository events) { this.events = events; }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void record(String actor, String action, String resourceType, Object resourceId, String result) {
        events.save(new AuditEvent(actor, action, resourceType, String.valueOf(resourceId), result));
    }
}
