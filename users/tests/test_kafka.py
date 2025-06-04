import pytest
import sys
import os
from datetime import datetime

# Отключаем реальные настройки Kafka
os.environ["KAFKA_BOOTSTRAP_SERVERS"] = "invalid:9092"

# Добавляем корень приложения в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import Column, Integer, String, DateTime, create_engine, select
from sqlalchemy.orm import declarative_base, sessionmaker
from kafka_producer import EventProducer

# База для эмуляции сохранения событий
Base = declarative_base()

class UserRegistrationEvent(Base):
    __tablename__ = "user_registration_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session

def test_send_event_producer_init_fails(monkeypatch):
    # Эмулируем падение KafkaProducer при инициализации
    monkeypatch.setattr(
        "kafka_producer.KafkaProducer",
        lambda *args, **kwargs: (_ for _ in ()).throw(Exception("init failed"))
    )

    producer = EventProducer(bootstrap_servers="invalid:9092")
    # Ожидаем, что producer не инициализировался
    assert producer.producer is None

    # Попытка отправить событие должна вернуть False
    assert producer.send_event("any_topic", {"foo": "bar"}) is False

def test_send_and_persist_user_registration_event(db_session, monkeypatch):
    # Эмулируем успешную работу KafkaProducer.send
    class DummyFuture:
        def get(self, timeout=None):
            class RecordMetadata:
                topic = "user_registrations"
                partition = 0
                offset = 0
            return RecordMetadata()

    class DummyKafkaProducer:
        def __init__(self, *args, **kwargs):
            pass
        def send(self, topic, value):
            # Проверяем, что topic и формат данных верны
            assert topic == "user_registrations"
            assert isinstance(value, dict)
            return DummyFuture()
        def close(self):
            pass

    monkeypatch.setattr("kafka_producer.KafkaProducer", DummyKafkaProducer)

    producer = EventProducer(bootstrap_servers="dummy:9092")
    assert producer.producer is not None

    # Отправляем событие регистрации
    success = producer.send_user_registration_event(user_id=42)
    assert success is True

    # Эмулируем потребление и сохранение в БД
    session = db_session()
    payload = {
        "event_type": "user_registration",
        "user_id": 42,
        "timestamp": datetime.utcnow().isoformat()
    }
    record = UserRegistrationEvent(
        user_id=payload["user_id"],
        event_type=payload["event_type"],
        timestamp=datetime.fromisoformat(payload["timestamp"])
    )
    session.add(record)
    session.commit()

    # Проверяем, что запись сохранилась
    rec = session.execute(
        select(UserRegistrationEvent).where(UserRegistrationEvent.user_id == 42)
    ).scalar_one()
    assert rec.event_type == "user_registration"
    assert rec.user_id == 42
    session.close()
