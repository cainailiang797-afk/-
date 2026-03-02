package com.example.EasyCar.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.EasyCar.common.JwtRedisUtil;
import com.example.EasyCar.common.PasswordConfig;
import com.example.EasyCar.domain.User;
import com.example.EasyCar.dto.LoginRequest;
import com.example.EasyCar.mapper.LoginMapper;
import com.example.EasyCar.service.LoginService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import javax.annotation.Resource;
import java.util.Date;

@Service
public class LoginServiceImpl implements LoginService {
    @Resource
    private LoginMapper loginMapper;
    
    @Autowired
    private JwtRedisUtil jwtRedisUtil;
    
    @Autowired
    private PasswordConfig passwordEncoder;
    
    public LoginRequest login(User user) {
        String username = user.getUsername();
        String password = user.getPassword();
        User getUserLogin = loginMapper.selectUserByusername(username);
        if (getUserLogin == null) {
            throw new RuntimeException("用户名错误，请注册");
        }
        
        boolean getVerify = verifyPassword(password, getUserLogin.getPassword());
        
        if (getVerify) {
            Long userId = getUserLogin.getId();
            String accessToken = jwtRedisUtil.generateAccessToken(userId);
            String refreshToken = jwtRedisUtil.generateValidRefreshToken(userId);
            
            
            LoginRequest loginRequest = new LoginRequest();
            loginRequest.setUsername(getUserLogin.getUsername());
            loginRequest.setAccessToken(accessToken);
            loginRequest.setRefreshToken(refreshToken);
            loginRequest.setCreate_time(getUserLogin.getCreateTime());
            
            return loginRequest;
        } else {
            throw new RuntimeException("用户名或密码错误");
        }
//        LoginRequest getLogin = loginMapper.login(user);
//        if (getLogin == null) {
//            throw new RuntimeException("密码错误");
//        }
        
    }
    
    //    注册
    public LoginRequest handleRegister(User user) {
        String username = user.getUsername();
        String password = encryPassword(user.getPassword());

        user.setPassword(password);
        user.setCreateTime(new Date());

        boolean success = loginMapper.InsertRegister(user);
        if (success) {
            User getUserLogin = loginMapper.selectUserByusername(username);

            Long userId = getUserLogin.getId();
            String accessToken = jwtRedisUtil.generateAccessToken(userId);
//                
            String refreshToken = jwtRedisUtil.generateAndSaveRefreshToken(userId);


            LoginRequest loginRequest = new LoginRequest();
//
            loginRequest.setAccessToken(accessToken);
            loginRequest.setRefreshToken(refreshToken);
            loginRequest.setUsername(username);
            loginRequest.setCreate_time(getUserLogin.getCreateTime());

            return loginRequest;
        } else {
            throw new RuntimeException("用户名或密码错误");
        }
    }
    
    public String encryPassword(String rawPassword) {
        return passwordEncoder.passwordEncoder().encode(rawPassword);
    }

    public Boolean verifyPassword(String rawPassword, String encodePassword) {
        return passwordEncoder.passwordEncoder().matches(rawPassword, encodePassword);
    }
    
    @Override
    public LoginRequest refreshToken(String refreshToken) {
        if (refreshToken == null || refreshToken.isEmpty()) {
            throw new RuntimeException("refreshToken不能为空");
        }
        
        if (!jwtRedisUtil.validateRefreshToken(refreshToken)) {
            throw new RuntimeException("refreshToken无效或已过期");
        }
        
        Long userId = Long.parseLong(jwtRedisUtil.getJtiFromRefreshToken(refreshToken));
        
        User user = loginMapper.selectUserById(userId);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }
        
        String newAccessToken = jwtRedisUtil.generateAccessToken(userId);
        
        LoginRequest loginRequest = new LoginRequest();
        loginRequest.setUsername(user.getUsername());
        loginRequest.setAccessToken(newAccessToken);
        loginRequest.setRefreshToken(refreshToken);
        
        return loginRequest;
    }
}
