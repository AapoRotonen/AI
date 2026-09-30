package com.supportai.domain.repo;

import com.supportai.domain.entity.ServiceStatus;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ServiceStatusRepository extends JpaRepository<ServiceStatus, String> { }
