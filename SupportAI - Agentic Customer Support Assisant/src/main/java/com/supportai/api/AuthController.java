package com.supportai.api;

import com.supportai.api.ApiDtos.LoginRequest;
import com.supportai.api.ApiDtos.LoginResponse;
import com.supportai.security.JwtService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
@Validated
public class AuthController {
    private final JwtService jwtService;
    public AuthController(JwtService jwtService) { this.jwtService = jwtService; }

    @PostMapping("/login")
    public LoginResponse login(@Valid @RequestBody LoginPayload payload) {
        return jwtService.login(payload.email(), payload.password());
    }

    public record LoginPayload(@NotBlank @Email @Size(max = 255) String email,
                               @NotBlank @Size(max = 200) String password) { }
}
