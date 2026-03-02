package com.example.EasyCar.service.impl;

import com.example.EasyCar.domain.Parking;
import com.example.EasyCar.mapper.ParkingMapper;
import com.example.EasyCar.service.ParkingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Date;
import java.util.List;

@Service
public class ParkingServiceImpl implements ParkingService {
    
    @Autowired
    public ParkingMapper parkingMapper;
    
    @Override
    public Boolean addParking(Parking parking) {
        try {
            return parkingMapper.addParking(parking);
        } catch (Exception e) {
            throw new RuntimeException("添加停车信息失败: " + e.getMessage());
        }
    }
    
    @Override
    public Parking findByPhoto(String photo) {
        try {
            return parkingMapper.findByPhoto(photo);
        } catch (Exception e) {
            throw new RuntimeException("查询停车信息失败: " + e.getMessage());
        }
    }
    
    @Override
    public List<Parking> findAll() {
        try {
            return parkingMapper.findAll();
        } catch (Exception e) {
            throw new RuntimeException("查询所有停车信息失败: " + e.getMessage());
        }
    }
    
    @Override
    public List<Parking> findByUserId(Long userId) {
        try {
            return parkingMapper.findByUserId(userId);
        } catch (Exception e) {
            throw new RuntimeException("查询用户停车信息失败: " + e.getMessage());
        }
    }
}
