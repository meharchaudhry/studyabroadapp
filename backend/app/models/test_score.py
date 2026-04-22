from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class TestScore(Base):
    __tablename__ = "user_tests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    test_name = Column(String, nullable=True)
    score = Column(Float, nullable=True)
    test_date = Column(String, nullable=True)

    user = relationship("User", back_populates="tests")