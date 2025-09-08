"""
Redis Subscriber 프레임워크

Author: Minseok kim
"""

import redis
import threading
import logging
from typing import Dict, Callable, Any


class RedisSubscriber:
    """Redis Queue에서 메시지를 구독하고 처리하는 프레임워크"""
    
    def __init__(self, redis_url: str, username: str = None, password: str = None):
        """
        RedisSubscriber 초기화
        
        Args:
            redis_url: Redis 연결 URL (예: "redis://localhost:6379")
            username: Redis 사용자명 (선택사항)
            password: Redis 비밀번호 (선택사항)
        """
        self.redis_url = redis_url
        self.username = username
        self.password = password
        self._handlers: Dict[str, Callable[[str], Any]] = {}
        self._threads: Dict[str, threading.Thread] = {}
        self._running = False
        self._redis_client = None
        
        # 로깅 설정
        self.logger = logging.getLogger(__name__)
    
    def subscribe(self, queue_name: str):
        """
        Queue 구독을 위한 데코레이터
        
        Args:
            queue_name: 구독할 Redis Queue 이름
            
        Returns:
            데코레이터 함수
        """
        def decorator(func: Callable[[str], Any]) -> Callable[[str], Any]:
            """
            데코레이터 함수
            
            Args:
                func: 등록할 핸들러 함수
                
            Returns:
                원본 함수
            """
            self._handlers[queue_name] = func
            self.logger.info(f"핸들러 등록됨: {queue_name} -> {func.__name__}")
            return func
        
        return decorator
    
    def start(self):
        """프레임워크 시작 - 모든 Queue Listener Thread 시작"""
        if self._running:
            self.logger.warning("프레임워크가 이미 실행 중입니다.")
            return
        
        # 이전에 실행된 적이 있다면 정리
        if self._threads:
            self.logger.info("이전 스레드 정보를 정리합니다.")
            self._threads.clear()
        
        try:
            # Redis 클라이언트 연결 (인증 정보 포함)
            connection_kwargs = {'decode_responses': True}
            
            # 인증 정보가 제공된 경우 추가
            if self.username:
                connection_kwargs['username'] = self.username
            if self.password:
                connection_kwargs['password'] = self.password
            
            self._redis_client = redis.from_url(self.redis_url, **connection_kwargs)
            self._redis_client.ping()  # 연결 테스트
            
            self._running = True
            
            # 각 큐별로 리스너 스레드 시작
            for queue_name in self._handlers.keys():
                thread = threading.Thread(
                    target=self._queue_listener,
                    args=(queue_name,),
                    name=f"QueueListener-{queue_name}",
                    daemon=True
                )
                thread.start()
                self._threads[queue_name] = thread
                self.logger.info(f"큐 리스너 스레드 시작됨: {queue_name}")
            
            self.logger.info("Redis Subscriber 프레임워크가 시작되었습니다.")
            
        except Exception as e:
            self.logger.error(f"프레임워크 시작 실패: {e}")
            self.stop()
            raise
    
    def stop(self):
        """프레임워크 종료 - 모든 Queue Listener Thread 안전 종료"""
        if not self._running:
            return
        
        self._running = False
        self.logger.info("프레임워크 종료 중...")
        
        # 모든 스레드가 종료될 때까지 대기
        for queue_name, thread in self._threads.items():
            if thread.is_alive():
                thread.join(timeout=1.0)
                self.logger.info(f"큐 리스너 스레드 종료됨: {queue_name}")
        
        # Redis 연결 종료
        if self._redis_client:
            self._redis_client.close()
            self._redis_client = None
        
        # 스레드 정보 정리
        self._threads.clear()
        self.logger.info("Redis Subscriber 프레임워크가 종료되었습니다.")
    
    def _queue_listener(self, queue_name: str):
        """
        Queue 리스너 스레드 메서드
        
        Args:
            queue_name: 리스닝할 큐 이름
        """
        handler = self._handlers[queue_name]
        
        while self._running:
            try:
                # BLPOP으로 메시지 대기 (1초 타임아웃)
                result = self._redis_client.blpop(queue_name, timeout=1)
                
                if result is not None:
                    # result는 (queue_name, message) 튜플
                    _, message = result
                    self.logger.debug(f"메시지 수신됨 [{queue_name}]: {message}")
                    
                    # 핸들러 함수 호출
                    try:
                        handler(message)
                    except Exception as e:
                        self.logger.error(f"핸들러 실행 중 에러 발생 [{queue_name}]: {e}")
                
            except Exception as e:
                if self._running:  # 의도적인 종료가 아닌 경우에만 에러 로그
                    self.logger.error(f"큐 리스너 에러 [{queue_name}]: {e}")
                break
        
        self.logger.debug(f"큐 리스너 스레드 종료됨: {queue_name}")
