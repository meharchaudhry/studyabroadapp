from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Degree(Base):
    __tablename__ = "user_degrees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    degree_level = Column(String, nullable=True)
    specialization = Column(String, nullable=True)
    cgpa = Column(Float, nullable=True)
    institution = Column(String, nullable=True)
    year_graduated = Column(String, nullable=True)

    user = relationship("User", back_populates="degrees")