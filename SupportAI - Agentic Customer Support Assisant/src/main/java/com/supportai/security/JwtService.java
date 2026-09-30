package com.supportai.security;

import com.supportai.api.ApiDtos.LoginResponse;
import com.supportai.domain.Role;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.oauth2.jose.jws.MacAlgorithm;
import org.springframework.security.oauth2.jwt.*;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.Duration;
import java.util.List;

@Service
public class JwtService {
    private final AuthenticationManager authenticationManager;
    private final JwtEncoder encoder;
    private final String issuer;
    private final Duration ttl;

    public JwtService(AuthenticationManager authenticationManager, JwtEncoder encoder,
                      @Value("${supportai.jwt.issuer}") String issuer,
                      @Value("${supportai.jwt.ttl}") Duration ttl) {
        this.authenticationManager = authenticationManager;
        this.encoder = encoder;
        this.issuer = issuer;
        this.ttl = ttl;
    }

    public LoginResponse login(String email, String password) {
        Authentication authentication = authenticationManager.authenticate(
                UsernamePasswordAuthenticationToken.unauthenticated(email, password));
        SupportPrincipal principal = (SupportPrincipal) authentication.getPrincipal();
        Instant now = Instant.now();
        Instant expiresAt = now.plus(ttl);
        List<String> roles = authentication.getAuthorities().stream().map(GrantedAuthority::getAuthority)
                .map(authority -> authority.substring("ROLE_".length())).toList();
        JwtClaimsSet claims = JwtClaimsSet.builder().issuer(issuer).issuedAt(now).expiresAt(expiresAt)
                .subject(principal.getUsername()).claim("roles", roles).build();
        String token = encoder.encode(JwtEncoderParameters.from(
                JwsHeader.with(MacAlgorithm.HS256).build(), claims)).getTokenValue();
        return new LoginResponse(token, "Bearer", expiresAt, principal.getUsername(), principal.role());
    }
}
