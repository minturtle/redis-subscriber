# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-09-08

### Added
- 초기 릴리즈
- Redis Queue 메시지 구독 기능
- 데코레이터 기반 핸들러 등록
- 멀티스레드 메시지 처리
- Redis 인증 지원 (username/password)
- 안전한 시작/종료 생명주기
- 포괄적인 통합 테스트

### Features
- `RedisSubscriber` 클래스로 간단한 API 제공
- `@subscriber.subscribe(queue_name)` 데코레이터로 핸들러 등록
- 각 큐별 독립적인 스레드로 메시지 처리
- BLPOP을 사용한 블로킹 메시지 대기
- 에러 발생 시에도 프레임워크 지속 동작
- 중복 start/stop 호출에 대한 안전성 보장

### Technical Details
- Python 3.9+ 지원
- redis-py 4.5.0+ 의존성
- TestContainers를 사용한 통합 테스트
- pytest 기반 테스트 프레임워크
