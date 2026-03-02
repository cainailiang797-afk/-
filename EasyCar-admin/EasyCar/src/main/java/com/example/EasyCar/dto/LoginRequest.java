package com.example.EasyCar.dto;

import lombok.Data;

import java.util.Date;

@Data
public class LoginRequest {
    private String username;
    private String accessToken;
    private String refreshToken;
    private Date create_time;
}
