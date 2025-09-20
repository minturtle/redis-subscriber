# Redis Subscriber

Redis Queue에서 메시지를 구독하고, 데코레이터를 통해 등록한 Python 함수에 메시지를 전달하는 최소 기능 프레임워크

## 특징

- 🚀 **간단한 API**: 데코레이터 기반 핸들러 등록
- 🔄 **멀티스레드**: 각 큐별 독립적인 스레드로 메시지 처리
- 🔐 **인증 지원**: Redis username/password 인증
- 🛡️ **안전한 종료**: 안전한 시작/종료 생명주기
- 📦 **최소 의존성**: redis-py만 필요

## 설치

### GitHub Release에서 설치

```bash
# 최신 릴리즈 설치
pip install git+https://github.com/minturtle/redis-subscriber.git@v1.0.1

# 또는 특정 브랜치에서 설치
pip install git+https://github.com/minturtle/redis-subscriber.git@main
```

### 소스에서 직접 설치

```bash
git clone https://github.com/minturtle/redis-subscriber.git
cd redis-subscriber
pip install -e .
```

### 개발 모드 설치

```bash
git clone https://github.com/minturtle/redis-subscriber.git
cd redis-subscriber
pip install -e ".[dev]"
```

## 사용법

### 기본 사용법

```python
from redis_subscriber import RedisSubscriber
import logging
logging.basicConfig(level=logging.INFO)

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

### 인증이 필요한 Redis 사용

```python
subscriber = RedisSubscriber(
    redis_url="redis://localhost:6379",
    username="myuser",
    password="mypassword"
)
```

## 요구사항

- Python >= 3.9
- Redis 서버
- redis-py >= 4.5.0

## 라이선스

MIT License

## 작성자

Minseok kim
