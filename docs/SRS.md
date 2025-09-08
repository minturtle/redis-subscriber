# Redis Subscriber 프레임워크 SRS

## 1. 소프트웨어 개요

### 1.1 목적
Redis Queue에서 메시지를 구독하고, 데코레이터를 통해 등록한 Python 함수에 메시지를 전달하는 최소 기능 프레임워크를 개발한다.

### 1.2 범위
- Redis Queue 메시지 구독 및 처리
- 데코레이터 기반 함수 등록
- 멀티스레드 메시지 처리
- 안전한 시작/종료 기능

### 1.3 기술 스택
- **언어:** Python ≥3.9
- **외부 의존:** `redis-py`

---

## 2. 기능 요구사항

### 2.1 FR-001: Redis Queue 구독
**우선순위:** 높음

**설명:** Redis Queue에서 메시지를 블로킹 방식으로 구독한다.

**세부 요구사항:**
- 각 Queue별로 별도 스레드에서 `BLPOP` 명령어를 사용한 블로킹 대기
- 메시지 수신 시 동기적으로 등록된 함수에 직접 전달
- 각 Queue는 독립적으로 메시지를 순차 처리

**입력:** Redis Queue 이름
**출력:** 메시지 문자열

### 2.2 FR-002: 데코레이터 기반 함수 등록
**우선순위:** 높음

**설명:** `@subscriber.subscribe()` 데코레이터를 통해 Queue별 처리 함수를 등록한다.

**세부 요구사항:**
- 데코레이터 문법으로 함수 등록
- Queue 이름을 데코레이터 인자로 전달
- 등록된 함수는 메시지 문자열을 첫 번째 인자로 받음

**사용 예시:**
```python
@subscriber.subscribe("queue1")
def handle_queue1(msg):
    print(msg)
```

### 2.3 FR-003: 멀티스레드 메시지 처리
**우선순위:** 높음

**설명:** Queue Listener Thread가 동기적으로 메시지를 처리한다.

**세부 요구사항:**
- **Queue Listener Thread:** 각 Queue에서 메시지 블로킹 대기
- 메시지 수신 시 등록된 함수에 직접 호출
- 동기적 순차 처리

**아키텍처:**
```
Main Thread
   |
   +-- Queue1 Listener Thread --> Handler Func A
   |
   +-- Queue2 Listener Thread --> Handler Func B
```

### 2.4 FR-004: 프레임워크 시작/종료
**우선순위:** 높음

**설명:** 프레임워크의 안전한 시작과 종료를 지원한다.

**세부 요구사항:**
- `start()`: 모든 Queue Listener Thread 시작
- `stop()`: 모든 Queue Listener Thread 안전 종료
- 종료 시 진행 중인 메시지 처리 완료 후 종료

### 2.5 FR-005: 에러 처리
**우선순위:** 중간

**설명:** 메시지 처리 중 발생하는 에러를 적절히 처리한다.

**세부 요구사항:**
- 함수 호출 중 에러 발생 시 로그 출력
- 에러 발생 시에도 프레임워크는 계속 동작
- 메시지 손실 방지 (ACK 기반이 아니므로 재처리는 제외)

---

## 3. 비기능 요구사항

### 3.1 NFR-001: 성능
- 메시지 처리 지연시간 최소화
- 각 Queue별 독립적인 순차 처리

### 3.2 NFR-002: 안정성
- 메시지 처리 중 에러 발생 시에도 프레임워크 중단 없음
- 안전한 종료 보장

### 3.3 NFR-003: 확장성
- Queue 개수에 제한 없음
- 각 Queue별 독립적인 처리

---

## 4. API 명세

### 4.1 RedisSubscriber 클래스

#### 생성자
```python
RedisSubscriber(redis_url: str)
```

**매개변수:**
- `redis_url`: Redis 연결 URL (예: "redis://localhost:6379")

#### 메서드

##### subscribe(queue_name: str)
**설명:** Queue 구독을 위한 데코레이터

**매개변수:**
- `queue_name`: 구독할 Redis Queue 이름

**반환값:** 데코레이터 함수

##### start()
**설명:** 프레임워크 시작

**매개변수:** 없음

**반환값:** 없음

##### stop()
**설명:** 프레임워크 종료

**매개변수:** 없음

**반환값:** 없음

---

## 5. 사용 예시

```python
from redis_subscriber import RedisSubscriber

# 프레임워크 초기화
subscriber = RedisSubscriber(redis_url="redis://localhost:6379")

# Queue별 처리 함수 등록
@subscriber.subscribe("queue1")
def handle_queue1(msg):
    print(f"Queue1 메시지: {msg}")

@subscriber.subscribe("queue2")
def handle_queue2(msg):
    print(f"Queue2 메시지: {msg}")

# 프레임워크 시작
subscriber.start()

# 종료 시
subscriber.stop()
```

---

## 6. 제외 사항

다음 기능들은 이번 버전에 포함하지 않음:
- Queue 추가/제거 (런타임)
- 메시지 재시도
- 우선순위 조정
- 메시지 필터링
- 배치 처리
- 메트릭 수집

---

## 7. 테스트 요구사항

### 7.1 단위 테스트
- RedisSubscriber 클래스의 각 메서드 테스트
- 데코레이터 등록 기능 테스트
- 에러 처리 테스트

### 7.2 통합 테스트
- Redis Queue와의 실제 통신 테스트
- 멀티스레드 동작 테스트
- 시작/종료 기능 테스트

### 7.3 성능 테스트
- 순차 메시지 처리 성능 테스트
- 메모리 사용량 테스트

---

**작성자:** Minseok kim  
**작성일:** 2025-09-08 
**버전:** 1.0
