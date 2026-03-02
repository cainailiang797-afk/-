package com.example.EasyCar.service;

import com.example.EasyCar.domain.Parking;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public interface ParkingService {
    Boolean addParking(Parking parking);
    
    Parking findByPhoto(String photo);
    
    List<Parking> findAll();
    
    List<Parking> findByUserId(Long userId);
}
