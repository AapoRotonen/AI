package com.supportai.domain.repo;

import com.supportai.domain.entity.CustomerOrder;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CustomerOrderRepository extends JpaRepository<CustomerOrder, Long> {
    List<CustomerOrder> findByCustomer_IdOrderByCreatedAtDesc(Long customerId);
    boolean existsByOrderNumber(String orderNumber);
}
