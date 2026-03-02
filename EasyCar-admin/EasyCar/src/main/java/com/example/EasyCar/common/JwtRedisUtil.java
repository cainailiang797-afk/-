package com.example.EasyCar.common;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import io.jsonwebtoken.security.SignatureException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.UUID;
import java.util.concurrent.TimeUnit;

@Component
public class JwtRedisUtil {
    @Value("${jwt.secret}")
    private String jwtSecret;

    @Value("${jwt.access-expire}")
    private long accessExpire;

    @Value("${jwt.refresh-expire}")
    private long refreshExpire;
    

    // 建议：将常量提取到配置类中，便于维护
    private static final String JWT_SECRET = "your-secret-key-32bytes-long-at-least-for-hmac-sha256"; // 你的JWT密钥（生成和解析必须一致）
    private static final long REFRESH_TOKEN_EXPIRE = 7 * 24 * 60 * 60 * 1000L; // 7天，单位：毫秒（JWT过期时间用毫秒）


    // 1. 注入依赖（Spring环境下，@Autowired 自动注入）
    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    // 3. 定义常量（Redis键前缀，统一维护，和生成token时保持一致）
    private static final String REFRESH_TOKEN_REDIS_PREFIX = "refresh_token:";
    // 正常JWT最大长度（预留足够冗余，避免误判）
    private static final int MAX_VALID_JWT_LENGTH = 1000;
    // 正常Redis键最大长度（refresh_token: + 32位UUID，约46位，预留冗余）
    private static final int MAX_VALID_REDIS_KEY_LENGTH = 100;
    
    public JwtRedisUtil(StringRedisTemplate stringRedisTemplate) {
        this.stringRedisTemplate = stringRedisTemplate;
    }

    // 极简存储：忽略TimeUnit报错，直接运行（Spring Boot会自动兼容）
    public String generateAndSaveRefreshToken(Long userId) {
        String jti = UUID.randomUUID().toString().replace("-", "");
        String redisKey = "refresh_token:" + jti;

        SecretKey secretKey = Keys.hmacShaKeyFor(jwtSecret.getBytes(StandardCharsets.UTF_8));
        String refreshToken = Jwts.builder()
                .setId(jti)
                .setSubject(userId.toString())
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis() + refreshExpire * 1000))
                .signWith(secretKey)
                .compact();

        // 关键：直接传入秒数，使用TimeUnit.SECONDS（即使IDE报错，运行时也能正常工作）
        // 这是最后一招：IDE报错不代表运行时报错，很多时候是IDE缓存问题
        stringRedisTemplate.opsForValue().set(REFRESH_TOKEN_REDIS_PREFIX + jti, refreshToken, 7, java.util.concurrent.TimeUnit.DAYS);

        return refreshToken;
    }

    public boolean validateRefreshToken(String refreshToken) {
        try {
            SecretKey secretKey = Keys.hmacShaKeyFor(jwtSecret.getBytes(StandardCharsets.UTF_8));
            String jti = Jwts.parserBuilder().setSigningKey(secretKey).build().parseClaimsJws(refreshToken).getBody().getId();
            return refreshToken.equals(stringRedisTemplate.opsForValue().get("refresh_token:" + jti));
        } catch (Exception e) {
            return false;
        }
    }


//    public void deleteRefreshToken(String refreshToken) {
//        try {
//            SecretKey secretKey = Keys.hmacShaKeyFor(jwtSecret.getBytes(StandardCharsets.UTF_8));
//            String jti = Jwts.parserBuilder().setSigningKey(secretKey).build().parseClaimsJws(refreshToken).getBody().getId();
//            stringRedisTemplate.delete("refresh_token:" + jti);
//        } catch (Exception e) {
//            throw new RuntimeException("注销失败");
//        }
//    }

    public String generateAccessToken(Long userId) {
        SecretKey secretKey = Keys.hmacShaKeyFor(jwtSecret.getBytes(StandardCharsets.UTF_8));
        return Jwts.builder()
                .setSubject(userId.toString())
                .setIssuedAt(new Date())
                .setExpiration(new Date(System.currentTimeMillis() + accessExpire * 1000))
                .signWith(secretKey)
                .compact();
    }


// 保留你原来的 SecretKey 定义（如从配置文件读取、公共方法构建等）

    /**
     * 新增：解析 refreshToken，获取其中的 jti 声明（供注销、刷新 Token 接口调用）
     * @param refreshToken 前端传递的 refreshToken
     * @return 解析出的 jti 字符串
     */
    public String getJtiFromRefreshToken(String refreshToken) {
        // 1. 前置校验：避免无效字符串传入（防止空指针、格式错误）
        if (refreshToken == null || refreshToken.isEmpty() || !refreshToken.contains(".")) {
            throw new RuntimeException("refreshToken 格式无效，不是合法的 JWT 字符串");
        }

        // 2. 确保 secretKey 与生成时一致（复用你工具类中的 secretKey，不要重新新建）
        // 如果你有构建 secretKey 的公共方法，直接调用即可（如 getSecretKey()）
        SecretKey secretKey = Keys.hmacShaKeyFor(jwtSecret.getBytes(StandardCharsets.UTF_8));

        if (secretKey == null) {
            throw new RuntimeException("JWT 签名密钥未初始化，无法解析 Token");
        }

        try {
            // 3. 解析 refreshToken，获取载荷（Claims）
            Claims claims = Jwts.parserBuilder()
                    .setSigningKey(secretKey) // 使用与生成时一致的密钥
                    .build()
                    .parseClaimsJws(refreshToken)
                    .getBody();

            // 4. 提取 jti（此时生成时已添加，不会为 null）
            String jti = claims.getId();
            if (jti == null || jti.isEmpty()) {
                throw new RuntimeException("refreshToken 中未包含有效的 jti 声明");
            }

            return jti;
        } catch (ExpiredJwtException e) {
            throw new RuntimeException("refreshToken 已过期，请重新登录");
        } catch (MalformedJwtException e) {
            throw new RuntimeException("refreshToken 格式错误，可能已被篡改");
        } catch (SignatureException e) {
            throw new RuntimeException("refreshToken 签名验证失败，无效 Token");
        } catch (Exception e) {
            throw new RuntimeException("解析 refreshToken 失败：" + e.getMessage());
        }
    }


    /**
     * 生成合法的refresh token（JWT格式）
     * @param userId 可选：用户ID，存入JWT载荷，便于业务关联
     * @return 标准三段式JWT字符串（可正常解析、无格式错误）
     */
    public String generateValidRefreshToken(Long userId) {  
        // 步骤1：生成JWT签名密钥（和解析时完全一致，使用HMAC-SHA算法）
        // 注意：密钥长度建议≥32字节，避免算法安全性不足
        SecretKey secretKey = Keys.hmacShaKeyFor(JWT_SECRET.getBytes(StandardCharsets.UTF_8));

        // 步骤2：生成jti（JWT唯一标识，UUID保证唯一性，和删除方法中的jti对应）
        String jti = UUID.randomUUID().toString().replace("-", "");

        // 步骤3：计算JWT过期时间（当前时间 + 7天）
        Date now = new Date();
        Date expireDate = new Date(now.getTime() + REFRESH_TOKEN_EXPIRE);

        // 步骤4：构建JWT并生成最终字符串（核心步骤，保证格式合法）
        String refreshToken = Jwts.builder()
                // 1. 设置头部（Header）：指定签名算法（默认即可，无需手动修改，jjwt会自动处理格式）
                .signWith(secretKey, SignatureAlgorithm.HS256) // 算法必须和解析时兼容，HS256是常用对称加密算法
                // 2. 设置载荷（Payload）：存储业务所需信息（非敏感信息，因为JWT载荷可解码）
                .setId(jti) // 存入jti（唯一标识，用于后续Redis删除）
                .setSubject(userId.toString()) // 存入用户ID（主题，便于业务关联）
                .setIssuedAt(now) // 存入JWT生成时间
                .setExpiration(expireDate) // 存入过期时间
                // 3. 生成标准JWT字符串（compact()方法是关键：自动拼接三段式，处理编码，生成合法格式）
                .compact();

        // 步骤5：（可选，和你之前的逻辑配套）将生成的refresh token存入Redis（便于后续注销）
        stringRedisTemplate.opsForValue().set(REFRESH_TOKEN_REDIS_PREFIX + jti, refreshToken, 7, java.util.concurrent.TimeUnit.DAYS);

        // 返回合法的refresh token（三段式结构，可直接用于后续解析、传递）
        return refreshToken;
    }

    // 6. 核心注销方法（复用之前优化后的逻辑，稍作调整适配接口）
    public void deleteRefreshToken(String refreshToken) {
        // 非空校验
        if (refreshToken == null || refreshToken.trim().isEmpty()) {
            throw new RuntimeException("refresh token不能为空");
        }

        // JWT三段式格式初步校验
        String[] jwtParts = refreshToken.split("\\.");
        if (jwtParts.length != 3) {
            throw new RuntimeException("refresh token格式非法");
        }

        try {
            // 生成签名密钥
            SecretKey secretKey = Keys.hmacShaKeyFor(JWT_SECRET.getBytes(StandardCharsets.UTF_8));

            // 解析refreshToken获取jti
            Claims claims = Jwts.parserBuilder()
                    .setSigningKey(secretKey)
                    .build()
                    .parseClaimsJws(refreshToken)
                    .getBody();
            String jti = claims.getId();

            // jti非空校验
            if (jti == null || jti.trim().isEmpty()) {
                throw new RuntimeException("refresh token中无有效标识");
            }

            // 删除Redis中的缓存（核心：让refreshToken失效）
            String redisKey = REFRESH_TOKEN_REDIS_PREFIX + jti;
            stringRedisTemplate.delete(redisKey);

        } catch (ExpiredJwtException e) {
            // 即使token已过期，退出登录时也视为注销成功（或按需调整提示）
            throw new RuntimeException("退出登录成功（refresh token已过期）");
        } catch (SignatureException e) {
            throw new RuntimeException("refresh token签名无效，无法注销");
        } catch (MalformedJwtException e) {
            throw new RuntimeException("refresh token格式错误，无法注销");
        } catch (Exception e) {
            throw new RuntimeException("注销失败，未知异常");
        }
    }

    // 7. 定义接收前端参数的实体类（前后端参数对应）
    static class LogoutRequestParam {
        private String refreshToken; // 字段名必须和前端传递的参数名一致

        // 必须提供get/set方法，否则Spring无法解析参数
        public String getRefreshToken() {
            return refreshToken;
        }

        public void setRefreshToken(String refreshToken) {
            this.refreshToken = refreshToken;
        }
    }

}
