"""
Redis Subscriber 프레임워크 통합 테스트 스위트

Author: Minseok kim
"""

import pytest
import time
import threading
import redis
from testcontainers.redis import RedisContainer
from redis_subscriber import RedisSubscriber


class TestRedisSubscriberIntegration:
    """Redis Subscriber 프레임워크 통합 테스트 클래스"""
    
    @pytest.fixture(scope="class")
    def redis_container(self):
        """Redis 컨테이너 픽스처 - 클래스 스코프로 한 번만 생성"""
        with RedisContainer("redis:7-alpine") as redis_container:
            yield redis_container
    
    @pytest.fixture
    def redis_client(self, redis_container):
        """Redis 클라이언트 픽스처"""
        client = redis.Redis(
            host=redis_container.get_container_host_ip(),
            port=redis_container.get_exposed_port(6379),
            decode_responses=True
        )
        # 연결 테스트
        client.ping()
        yield client
        # 테스트 후 정리
        client.flushall()
        client.close()
    
    @pytest.fixture
    def subscriber(self, redis_container):
        """RedisSubscriber 인스턴스 픽스처"""
        redis_url = f"redis://{redis_container.get_container_host_ip()}:{redis_container.get_exposed_port(6379)}"
        subscriber = RedisSubscriber(redis_url=redis_url)
        yield subscriber
        # 테스트 후 정리
        try:
            subscriber.stop()
        except:
            pass
    
    @pytest.fixture
    def test_queue_name(self):
        """테스트용 큐 이름"""
        return "test_queue"
    
    @pytest.fixture
    def test_message(self):
        """테스트용 메시지 데이터"""
        return "test_message_content"


class TestBasicFunctionality(TestRedisSubscriberIntegration):
    """기본 기능 통합 테스트"""
    
    def test_subscribe_decorator_registration(self, subscriber, test_queue_name):
        """
        테스트 케이스: @subscribe 데코레이터를 통한 함수 등록
        - 데코레이터로 함수가 정상 등록되는지 확인
        - 등록된 함수가 올바른 큐와 매핑되는지 확인
        """
        # 테스트용 핸들러 함수
        received_messages = []
        
        @subscriber.subscribe(test_queue_name)
        def test_handler(msg):
            received_messages.append(msg)
        
        # 등록된 핸들러가 있는지 확인
        assert hasattr(subscriber, '_handlers')
        assert test_queue_name in subscriber._handlers
        assert subscriber._handlers[test_queue_name] == test_handler
    
    def test_start_stop_lifecycle(self, subscriber, redis_client, test_queue_name):
        """
        테스트 케이스: 프레임워크 시작/종료 생명주기
        - start() 호출 시 모든 큐 리스너 스레드가 정상 시작되는지 확인
        - stop() 호출 시 모든 큐 리스너 스레드가 안전하게 종료되는지 확인
        - 중복 start/stop 호출에 대한 안전성 확인
        """
        # 핸들러 등록
        received_messages = []
        
        @subscriber.subscribe(test_queue_name)
        def test_handler(msg):
            received_messages.append(msg)
        
        # 프레임워크 시작
        subscriber.start()
        
        # 스레드가 시작되었는지 확인
        assert hasattr(subscriber, '_threads')
        assert test_queue_name in subscriber._threads
        assert subscriber._threads[test_queue_name].is_alive()
        
        # 메시지 전송하여 정상 동작 확인
        redis_client.lpush(test_queue_name, "test_message")
        time.sleep(0.1)  # 메시지 처리 대기
        
        # 프레임워크 종료
        subscriber.stop()
        
        # 스레드가 종료되었는지 확인
        time.sleep(0.1)  # 스레드 종료 대기
        assert not subscriber._threads[test_queue_name].is_alive()
        
        # 중복 start/stop 호출 안전성 확인
        subscriber.start()
        subscriber.stop()
        subscriber.start()
        subscriber.stop()
        
        # 메시지가 정상 처리되었는지 확인
        assert len(received_messages) >= 1
        assert "test_message" in received_messages


class TestMessageProcessing(TestRedisSubscriberIntegration):
    """메시지 처리 통합 테스트"""
    
    def test_message_processing_and_threading(self, subscriber, redis_client):
        """
        테스트 케이스: 메시지 처리 및 스레딩
        - 단일/다중 큐 메시지 처리 확인
        - 각 큐별로 별도 스레드가 생성되는지 확인
        - 큐 간 메시지 혼선이 없는지 확인
        """
        # 각 큐별 메시지 수신을 위한 리스트
        queue1_messages = []
        queue2_messages = []
        queue3_messages = []
        
        # 스레드 정보를 저장할 리스트
        thread_info = []
        
        # 여러 큐에 핸들러 등록
        @subscriber.subscribe("test_queue1")
        def handler1(msg):
            queue1_messages.append(msg)
            thread_info.append({
                'queue': 'queue1',
                'thread_id': threading.current_thread().ident
            })
        
        @subscriber.subscribe("test_queue2")
        def handler2(msg):
            queue2_messages.append(msg)
            thread_info.append({
                'queue': 'queue2',
                'thread_id': threading.current_thread().ident
            })
        
        @subscriber.subscribe("test_queue3")
        def handler3(msg):
            queue3_messages.append(msg)
            thread_info.append({
                'queue': 'queue3',
                'thread_id': threading.current_thread().ident
            })
        
        # 프레임워크 시작
        subscriber.start()
        
        # 각 큐에 메시지 전송
        redis_client.lpush("test_queue1", "msg1_1")
        redis_client.lpush("test_queue1", "msg1_2")
        redis_client.lpush("test_queue2", "msg2_1")
        redis_client.lpush("test_queue3", "msg3_1")
        
        # 메시지 처리 대기
        time.sleep(0.5)
        
        # 프레임워크 종료
        subscriber.stop()
        
        # 스레드 격리 확인
        assert len(thread_info) == 4
        thread_ids = [info['thread_id'] for info in thread_info]
        assert len(set(thread_ids)) == 3  # 3개의 서로 다른 스레드 ID
        
        # 메시지 처리 확인
        assert len(queue1_messages) == 2
        assert len(queue2_messages) == 1
        assert len(queue3_messages) == 1
        
        # 큐 간 메시지 혼선이 없는지 확인
        assert not any("queue1" in msg for msg in queue2_messages + queue3_messages)
        assert not any("queue2" in msg for msg in queue1_messages + queue3_messages)
        assert not any("queue3" in msg for msg in queue1_messages + queue2_messages)


class TestErrorHandling(TestRedisSubscriberIntegration):
    """에러 처리 통합 테스트"""
    
    def test_handler_function_error_handling(self, subscriber, redis_client, test_queue_name):
        """
        테스트 케이스: 핸들러 함수 에러 처리
        - 핸들러 함수에서 예외 발생 시 로그가 출력되는지 확인
        - 에러 발생 후에도 프레임워크가 계속 동작하는지 확인
        - 다음 메시지 처리가 정상적으로 이루어지는지 확인
        """
        # 에러 발생 횟수와 정상 메시지 수신을 위한 카운터
        error_count = 0
        success_count = 0
        received_messages = []
        
        @subscriber.subscribe(test_queue_name)
        def error_prone_handler(msg):
            nonlocal error_count, success_count
            received_messages.append(msg)
            
            # 첫 번째와 세 번째 메시지에서 에러 발생
            if msg == "error_message" or msg == "another_error_message":
                error_count += 1
                raise ValueError(f"의도된 에러: {msg}")
            else:
                success_count += 1
        
        # 프레임워크 시작
        subscriber.start()
        
        # 에러를 발생시키는 메시지와 정상 메시지 전송
        test_messages = [
            "error_message",           # 에러 발생
            "normal_message_1",        # 정상 처리
            "another_error_message",   # 에러 발생
            "normal_message_2",        # 정상 처리
            "normal_message_3"         # 정상 처리
        ]
        
        for msg in test_messages:
            redis_client.lpush(test_queue_name, msg)
        
        # 메시지 처리 대기
        time.sleep(0.5)
        
        # 프레임워크 종료
        subscriber.stop()
        
        # 에러가 발생했지만 프레임워크가 계속 동작했는지 확인
        assert error_count == 2  # 2개의 에러 메시지
        assert success_count == 3  # 3개의 정상 메시지
        assert len(received_messages) == 5  # 모든 메시지가 수신됨
        
        # 정상 메시지들이 올바르게 처리되었는지 확인
        assert "normal_message_1" in received_messages
        assert "normal_message_2" in received_messages
        assert "normal_message_3" in received_messages
    
    def test_redis_connection_error_handling(self):
        """
        테스트 케이스: Redis 연결 에러 처리
        - Redis 서버 연결 실패 시 적절한 에러 처리 확인
        """
        # 잘못된 Redis URL로 subscriber 생성
        invalid_subscriber = RedisSubscriber(redis_url="redis://invalid_host:6379")
        
        # 핸들러 등록
        @invalid_subscriber.subscribe("test_queue")
        def test_handler(msg):
            pass
        
        # 연결 실패 시 적절한 에러가 발생하는지 확인
        with pytest.raises(Exception):  # Redis 연결 에러
            invalid_subscriber.start()
    
    def test_handler_function_timeout_handling(self, subscriber, redis_client, test_queue_name):
        """
        테스트 케이스: 핸들러 함수 타임아웃 처리
        - 핸들러 함수가 오래 걸려도 프레임워크가 계속 동작하는지 확인
        """
        received_messages = []
        
        @subscriber.subscribe(test_queue_name)
        def slow_handler(msg):
            received_messages.append(msg)
            # 의도적으로 처리 시간을 늘림
            time.sleep(0.2)
        
        # 프레임워크 시작
        subscriber.start()
        
        # 여러 메시지 전송
        test_messages = ["slow_msg_1", "slow_msg_2", "slow_msg_3"]
        for msg in test_messages:
            redis_client.lpush(test_queue_name, msg)
        
        # 충분한 시간 대기 (순차 처리되므로 0.6초 이상 필요)
        time.sleep(1.0)
        
        # 프레임워크 종료
        subscriber.stop()
        
        # 모든 메시지가 순차적으로 처리되었는지 확인
        assert len(received_messages) == 3
        for msg in test_messages:
            assert msg in received_messages
    

    



class TestRealWorldScenarios(TestRedisSubscriberIntegration):
    """실제 사용 시나리오 통합 테스트"""
    
    def test_comprehensive_scenarios(self, subscriber, redis_client, test_queue_name):
        """
        테스트 케이스: 종합 시나리오 테스트
        - 다양한 메시지 타입 처리
        - 빠른 시작/종료 반복
        - 대량 메시지 처리
        - 실제 워크플로우 시뮬레이션
        """
        # 1. 다양한 메시지 타입 처리 테스트
        received_messages = []
        
        @subscriber.subscribe(test_queue_name)
        def test_handler(msg):
            received_messages.append(msg)
        
        # 프레임워크 시작
        subscriber.start()
        
        # 다양한 타입의 메시지들
        test_messages = [
            "일반 문자열",
            "한글 메시지 테스트",
            "특수문자: !@#$%^&*()_+-=[]{}|;':\",./<>?",
            "유니코드: 🚀🔥💯🎉",
            "매우 긴 메시지 " * 50,  # 긴 메시지
            "",  # 빈 문자열
        ]
        
        # 메시지 전송
        for msg in test_messages:
            redis_client.lpush(test_queue_name, msg)
        
        # 대량 메시지 추가 (20개)
        for i in range(20):
            redis_client.lpush(test_queue_name, f"bulk_message_{i}")
        
        # 메시지 처리 대기
        time.sleep(1.0)
        
        # 프레임워크 종료
        subscriber.stop()
        
        # 메시지 처리 확인
        assert len(received_messages) == len(test_messages) + 20
        for msg in test_messages:
            assert msg in received_messages
        
        # 2. 빠른 시작/종료 반복 테스트
        for i in range(3):
            subscriber.start()
            redis_client.lpush(test_queue_name, f"cycle_{i}_msg")
            time.sleep(0.1)
            subscriber.stop()
            time.sleep(0.1)
        
        # 3. 실제 워크플로우 시뮬레이션
        orders = []
        emails = []
        
        @subscriber.subscribe("order_queue")
        def process_order(order_data):
            orders.append(order_data)
            redis_client.lpush("email_queue", f"order_confirmation_{order_data}")
        
        @subscriber.subscribe("email_queue")
        def send_email(email_data):
            emails.append(email_data)
        
        subscriber.start()
        
        # 주문 데이터 전송
        order_ids = ["ORDER_001", "ORDER_002"]
        for order_id in order_ids:
            redis_client.lpush("order_queue", order_id)
        
        time.sleep(0.5)
        subscriber.stop()
        
        # 워크플로우 확인
        assert len(orders) == 2
        assert len(emails) == 2
        for order_id in order_ids:
            assert order_id in orders
            assert f"order_confirmation_{order_id}" in emails


# 테스트 실행을 위한 메인 함수
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
