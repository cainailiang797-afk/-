package com.example.EasyCar.common;

import lombok.Getter;

/**
 * 统一状态码枚举类（依赖 lombok，需确保插件和依赖生效）
 */
@Getter // 确保 lombok 能生成 getter 方法
public enum ResultCode {
    // 注意：逗号分隔，最后一个加 分号
    SUCCESS(200, "操作成功"),
    PARAM_ERROR(400, "参数格式错误"),
    RESOURCE_NOT_FOUND(404, "请求资源不存在"),
    SERVER_ERROR(500, "服务器内部错误"); // 🔥 关键：分号不可少

    // 私有 final 字段
    private final Integer code;
    private final String msg;

    // 私有构造方法（可省略 private）
    ResultCode(Integer code, String msg) {
        this.code = code;
        this.msg = msg;
    }
}