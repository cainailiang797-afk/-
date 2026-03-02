package com.example.EasyCar.common;

import lombok.Data;

@Data
public class Result<T> {
    // 状态码
    private Integer code;
    // 提示信息
    private String msg;
    // 业务数据
    private T data;
    
    private Result() {}
    
    public static <T> Result<T> success(T data) {
        Result<T> result = new Result<>();
        result.setCode(ResultCode.SUCCESS.getCode());
        result.setMsg(ResultCode.SUCCESS.getMsg());
        result.setData(data);
        return result;
    }
    
    public static <T> Result<T> success() {
        return success(null);
    }
    
    public static <T> Result<T> success(String msg) {
        Result<T> result = new Result<>();
        result.setCode(ResultCode.SUCCESS.getCode());
        result.setMsg(msg);
        result.setData(null);
        return result;
    }
    
    public static <T> Result<T> success(String msg, T data) {
        Result<T> result = new Result<>();
        result.setCode(ResultCode.SUCCESS.getCode());
        result.setMsg(msg);
        result.setData(data);
        return result;
    }

    public static <T> Result<T> error(ResultCode resultCode) {
        Result<T> result = new Result<>();
        result.setCode(resultCode.getCode());
        result.setMsg(resultCode.getMsg());
        result.setData(null);
        return result;
    }

    // 核对这个方法是否存在且正确
    public static <T> Result<T> error(ResultCode resultCode, String customMsg) {
        Result<T> result = new Result<>();
        result.setCode(resultCode.getCode());
        result.setMsg(customMsg); // 不能为 null，否则返回格式会异常
        result.setData(null);
        return result;
    }
}
