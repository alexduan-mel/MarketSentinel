package com.sentinelstream;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.redis.connection.RedisConnectionFactory;

@Slf4j
@SpringBootApplication
public class ExecutionerApplication implements CommandLineRunner {

    private final RedisConnectionFactory redisConnectionFactory;

    public ExecutionerApplication(RedisConnectionFactory redisConnectionFactory) {
        this.redisConnectionFactory = redisConnectionFactory;
    }

    public static void main(String[] args) {
        SpringApplication.run(ExecutionerApplication.class, args);
    }

    @Override
    public void run(String... args) {
        try {
            redisConnectionFactory.getConnection().ping();
            System.out.println("Sentinel-Java: Redis Connection [OK]");
        } catch (Exception e) {
            System.out.println("Sentinel-Java: Redis Connection [FAIL]");
        }
    }
}
