package com.supportai.security;

import com.supportai.domain.repo.AppUserRepository;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Service
public class SupportUserDetailsService implements UserDetailsService {
    private final AppUserRepository users;

    public SupportUserDetailsService(AppUserRepository users) { this.users = users; }

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        return users.findByEmailIgnoreCase(username)
                .map(user -> new SupportPrincipal(user.getId(), user.getEmail(), user.getPasswordHash(), user.getRole()))
                .orElseThrow(() -> new UsernameNotFoundException("Invalid credentials."));
    }
}
