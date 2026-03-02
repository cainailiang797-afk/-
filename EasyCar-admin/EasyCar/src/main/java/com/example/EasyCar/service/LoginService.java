package com.example.EasyCar.service;

import com.example.EasyCar.domain.User;
import com.example.EasyCar.dto.LoginRequest;
import org.springframework.stereotype.Service;

@Service
public interface LoginService {
    LoginRequest login(User user);

    // 注册
    LoginRequest handleRegister(User user);
    
    // 刷新Token
    LoginRequest refreshToken(String refreshToken);
}
