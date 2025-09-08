"""
Redis Subscriber 프레임워크

Redis Queue에서 메시지를 구독하고, 데코레이터를 통해 등록한 Python 함수에 메시지를 전달하는 최소 기능 프레임워크

Author: Minseok kim
"""

from .subscriber import RedisSubscriber

__version__ = "1.0.0"
__author__ = "Minseok kim"
__all__ = ["RedisSubscriber"]
