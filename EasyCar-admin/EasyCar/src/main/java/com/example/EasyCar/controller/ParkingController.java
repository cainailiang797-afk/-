package com.example.EasyCar.controller;

import com.example.EasyCar.common.JwtRedisUtil;
import com.example.EasyCar.common.Result;
import com.example.EasyCar.common.ResultCode;
import com.example.EasyCar.domain.Parking;
import com.example.EasyCar.service.ParkingService;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.List;

@RestController
@RequestMapping("/api")
public class ParkingController {
    
    @Autowired
    public ParkingService parkingService;
    
    @Autowired
    private JwtRedisUtil jwtRedisUtil;
    
    @Value("${jwt.secret}")
    private String jwtSecret;
    
    private Long getUserIdFromToken(String token) {
        SecretKey secretKey = Keys.hmacShaKeyFor(jwtSecret.getBytes(StandardCharsets.UTF_8));
        Claims claims = Jwts.parserBuilder()
                .setSigningKey(secretKey)
                .build()
                .parseClaimsJws(token)
                .getBody();
        return Long.parseLong(claims.getSubject());
    }
    
    @PostMapping("add")
    public Result<Parking> addParking(@RequestHeader("Authorization") String token,
                                      @RequestParam String photo,
                                      @RequestParam String parkingLocation,
                                      @RequestParam String location) {
        String tokenStr = token.replace("Bearer ", "");
        Long userId = getUserIdFromToken(tokenStr);
        
        Parking parking = new Parking();
        parking.setUserId(userId);
        parking.setPhoto(photo);
        parking.setParkingLocation(parkingLocation);
        parking.setLocation(location);
        parking.setCreateTime(new Date());
        
        Boolean isAddParking = parkingService.addParking(parking);
        if (isAddParking) {
            return Result.success("定位成功！");
        } else {
            return Result.error(ResultCode.SERVER_ERROR, "定位失败！");
        }
    }
    
    @GetMapping("find")
    public Result<Parking> findByPhoto(@RequestHeader("Authorization") String token,
                                      @RequestParam String photo) {
        String tokenStr = token.replace("Bearer ", "");
        Long userId = getUserIdFromToken(tokenStr);
        
        Parking parking = parkingService.findByPhoto(photo);
        if (parking != null && parking.getUserId().equals(userId)) {
            return Result.success(parking);
        } else {
            return Result.error(ResultCode.SERVER_ERROR, "未找到该车辆的停车信息！");
        }
    }
    
    @GetMapping("list")
    public Result<List<Parking>> findAll(@RequestHeader("Authorization") String token) {
        String tokenStr = token.replace("Bearer ", "");
        Long userId = getUserIdFromToken(tokenStr);
        
        List<Parking> list = parkingService.findByUserId(userId);
        return Result.success(list);
    }
    
}
