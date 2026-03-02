package com.example.EasyCar.mapper;

import com.example.EasyCar.domain.Parking;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface ParkingMapper {
    boolean addParking(Parking parking);
    
    Parking findByPhoto(String photo);
    
    List<Parking> findAll();
    
    List<Parking> findByUserId(Long userId);
}
