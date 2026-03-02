package com.example.EasyCar.mapper;

import com.example.EasyCar.domain.User;
import com.example.EasyCar.dto.LoginRequest;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface LoginMapper {
    User selectUserByusername(String username);
    
    User selectUserById(Long id);
    
    LoginRequest login(User user);
    Boolean InsertRegister(User user);
}
