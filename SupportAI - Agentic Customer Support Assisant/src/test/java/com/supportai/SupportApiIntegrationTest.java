package com.supportai;

import com.supportai.api.ApiDtos.LoginResponse;
import com.supportai.api.ApiDtos.TicketView;
import com.supportai.domain.TicketStatus;
import com.supportai.domain.repo.SupportTicketRepository;
import com.supportai.service.HumanReviewService;
import com.supportai.service.TicketService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.*;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.util.List;
import java.nio.charset.StandardCharsets;
import java.util.Base64;

import static org.assertj.core.api.Assertions.assertThat;

@Testcontainers(disabledWithoutDocker = true)
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
class SupportApiIntegrationTest {
    @Container
    static final PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("pgvector/pgvector:pg16");

    @DynamicPropertySource
    static void databaseProperties(DynamicPropertyRegistry registry) {
        registry.add("DB_URL", postgres::getJdbcUrl);
        registry.add("DB_USERNAME", postgres::getUsername);
        registry.add("DB_PASSWORD", postgres::getPassword);
        registry.add("spring.ai.openai.api-key", () -> "supportai-disabled");
        registry.add("supportai.ai.api-key", () -> "supportai-disabled");
        registry.add("DEMO_AGENT_PASSWORD", () -> "AgentDemo123!");
        registry.add("DEMO_SENIOR_PASSWORD", () -> "SeniorDemo123!");
        registry.add("DEMO_OTHER_PASSWORD", () -> "OtherDemo123!");
    }

    @Autowired TestRestTemplate http;
    @Autowired HumanReviewService reviews;
    @Autowired SupportTicketRepository tickets;

    @AfterEach
    void clearSecurityContext() { SecurityContextHolder.clearContext(); }

    @Test
    void loginAndTicketApiEnforceAssignmentAuthorization() {
        LoginResponse login = login("agent@supportai.demo", "AgentDemo123!");
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(login.accessToken());
        ResponseEntity<List<TicketView>> response = http.exchange("/api/tickets", HttpMethod.GET,
                new HttpEntity<>(headers), new ParameterizedTypeReference<>() { });

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        assertThat(response.getBody()).extracting(TicketView::id).containsExactlyInAnyOrder(1001L, 1002L, 1003L);
        ResponseEntity<String> denied = http.exchange("/api/tickets/2002", HttpMethod.GET,
                new HttpEntity<>(headers), String.class);
        assertThat(denied.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        for (String suffix : List.of("history", "customer", "orders")) {
            ResponseEntity<String> relatedDenied = http.exchange("/api/tickets/2002/" + suffix, HttpMethod.GET,
                    new HttpEntity<>(headers), String.class);
            assertThat(relatedDenied.getStatusCode()).isEqualTo(HttpStatus.NOT_FOUND);
        }
    }

    @Test
    void editedRoleClaimCannotEscalateJwtPrivileges() {
        LoginResponse login = login("agent@supportai.demo", "AgentDemo123!");
        String[] parts = login.accessToken().split("\\.");
        String forgedPayload = Base64.getUrlEncoder().withoutPadding().encodeToString(
                "{\"iss\":\"supportai\",\"sub\":\"agent@supportai.demo\",\"roles\":[\"ADMIN\"]}"
                        .getBytes(StandardCharsets.UTF_8));
        String forgedToken = parts[0] + "." + forgedPayload + "." + parts[2];
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(forgedToken);
        ResponseEntity<String> response = http.exchange("/api/tickets", HttpMethod.GET, new HttpEntity<>(headers), String.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.UNAUTHORIZED);
    }

    @Test
    void onlyASecondHumanCanApproveAndApprovedCloseIsDeterministic() {
        as("agent@supportai.demo", "ROLE_SUPPORT_AGENT");
        var pending = reviews.propose(1001L, "CLOSE_TICKET", "The support issue has been resolved.");
        assertThat(pending.status().name()).isEqualTo("PENDING");

        org.assertj.core.api.Assertions.assertThatThrownBy(() -> reviews.approve(pending.id(), "self approval"))
                .isInstanceOf(org.springframework.security.access.AccessDeniedException.class);
        as("senior@supportai.demo", "ROLE_SENIOR_SUPPORT");
        var approved = reviews.approve(pending.id(), "Reviewed and approved.");
        assertThat(approved.status().name()).isEqualTo("APPROVED");
        assertThat(tickets.findById(1001L).orElseThrow().getStatus()).isEqualTo(TicketStatus.CLOSED);
    }

    private LoginResponse login(String email, String password) {
        ResponseEntity<LoginResponse> response = http.postForEntity("/api/auth/login", new LoginPayload(email, password), LoginResponse.class);
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.OK);
        return response.getBody();
    }

    private void as(String email, String role) {
        SecurityContextHolder.getContext().setAuthentication(UsernamePasswordAuthenticationToken.authenticated(
                email, "test", List.of(new SimpleGrantedAuthority(role))));
    }

    private record LoginPayload(String email, String password) { }
}
