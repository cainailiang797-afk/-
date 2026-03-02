package com.example.EasyCar.controller;

import com.example.EasyCar.common.Result;
import com.example.EasyCar.common.ResultCode;
import com.example.EasyCar.domain.User;
import com.example.EasyCar.dto.LoginRequest;
import com.example.EasyCar.service.LoginService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class LoginController {
    @Autowired
    private LoginService loginService;
    
    @PostMapping("/login")
    public Result<LoginRequest> login(@RequestBody User user) {
        LoginRequest tokenMap = loginService.login(user);
        if (tokenMap != null) {
            return Result.success("登录成功", tokenMap);
        } else {
            return Result.error(ResultCode.SERVER_ERROR, "登录失败");
        }
    }

    @PostMapping("/register")
    public Result<LoginRequest> register(@RequestBody User user) {
        LoginRequest tokenMap = loginService.handleRegister(user);
        if (tokenMap != null) {
            return Result.success("注册成功", tokenMap);
        } else {
            return Result.error(ResultCode.SERVER_ERROR, "注册失败");
        }
    }
    
    @PostMapping("/refresh")
    public Result<LoginRequest> refreshToken(@RequestBody String refreshToken) {
        try {
            LoginRequest tokenMap = loginService.refreshToken(refreshToken);
            return Result.success("刷新成功", tokenMap);
        } catch (Exception e) {
            return Result.error(ResultCode.SERVER_ERROR, e.getMessage());
        }
    }
}
