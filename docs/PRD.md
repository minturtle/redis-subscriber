# Redis Subscriber 프레임워크 PRD

## 1. 개요

* **목적:** Redis Queue에서 메시지를 구독하고, 데코레이터를 통해 등록한 Python 함수에 메시지를 전달하는 최소 기능 프레임워크
* **언어:** Python ≥3.9
* **외부 의존:** `redis-py`

---

## 2. 핵심 기능

### 2.1 Redis Queue 대기

* 각 Queue별로 **별도 스레드**에서 블로킹 대기 (`BLPOP`)
* 메시지 수신 시 동기적으로 등록된 함수에 직접 전달
* 각 Queue는 독립적으로 메시지를 순차 처리

---

### 2.2 데코레이터를 통한 함수 등록

* 사용 예시:

```python
@subscriber.subscribe("queue1")
def handle_queue1(msg):
    ...

@subscriber.subscribe("queue2")
def handle_queue2(msg):
    ...
```

---

### 2.3 멀티스레드 구조

* **Queue Listener Thread (스레드별)**
  * 각 Queue에서 메시지 블로킹 대기
  * 메시지 수신 시 등록된 함수에 직접 호출
  * 동기적 순차 처리

**다이어그램**

```
Main Thread
   |
   +-- Queue1 Listener Thread --> Handler Func A
   |
   +-- Queue2 Listener Thread --> Handler Func B
```

---

### 2.4 메시지 전달 규칙

* 메시지는 Redis Queue의 문자열 형태 그대로 전달
* 함수 호출 시: 메시지 문자열이 첫 번째 인자로 전달

---

### 2.5 최소 API

```python
subscriber = RedisSubscriber(redis_url="redis://localhost:6379")

@subscriber.subscribe("queue1")
def handle_queue1(msg):
    print(msg)

subscriber.start()  # Queue별 대기 스레드 시작
subscriber.stop()   # 안전하게 종료
```

---

## 3. 고려 사항

1. **에러 처리:**

   * 함수 호출 중 에러 발생 시 로그 출력
   * 메시지 손실 방지(ACK 기반이 아니므로 재처리는 제외)
2. **종료 처리:**

   * `stop()` 호출 시 모든 Queue Listener Thread 안전 종료
3. **확장성 제한:**

   * Queue 추가/제거, 메시지 재시도, 우선순위 조정 등은 포함하지 않음

