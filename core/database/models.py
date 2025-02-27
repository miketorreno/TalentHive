from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import (
    ARRAY,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    BigInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[str] = mapped_column(BigInteger, nullable=False)
    role_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(String)
    username: Mapped[Optional[str]] = mapped_column(String)
    gender: Mapped[str] = mapped_column(String, nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String)
    email: Mapped[Optional[str]] = mapped_column(String)
    password: Mapped[Optional[str]] = mapped_column(String)
    country: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    cv_url: Mapped[Optional[str]] = mapped_column(String)
    education: Mapped[Optional[dict]] = mapped_column(JSONB, index=True)
    experience: Mapped[Optional[dict]] = mapped_column(JSONB, index=True)
    expertise: Mapped[Optional[dict]] = mapped_column(JSONB, index=True)
    portfolios: Mapped[Optional[dict]] = mapped_column(JSONB)
    user_preferences: Mapped[Optional[dict]] = mapped_column(JSONB)
    subscribed_alerts: Mapped[Optional[list]] = mapped_column(ARRAY(String))
    verified_user: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    company: Mapped[Optional["Company"]] = relationship(back_populates="employees")
    jobs: Mapped[List["Job"]] = relationship(back_populates="employer")
    applications: Mapped[List["Application"]] = relationship(back_populates="candidate")
    saved_jobs: Mapped[List["SavedJob"]] = relationship(back_populates="user")
    skills: Mapped[List["Skill"]] = relationship(
        secondary="user_skills", back_populates="users"
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("categories.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=True,
    )
    category_name: Mapped[str] = mapped_column(String, nullable=False)
    category_description: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    jobs: Mapped[List["Job"]] = relationship(back_populates="category")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    company_type: Mapped[Optional[str]] = mapped_column(String)
    startup_type: Mapped[Optional[str]] = mapped_column(String)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    company_description: Mapped[Optional[str]] = mapped_column(Text)
    trade_license: Mapped[Optional[str]] = mapped_column(String)
    employer_photo: Mapped[Optional[str]] = mapped_column(String)
    company_website: Mapped[Optional[str]] = mapped_column(String)
    company_industry: Mapped[Optional[str]] = mapped_column(String)
    company_status: Mapped[str] = mapped_column(
        String,
        default="pending",
    )
    verified_company: Mapped[bool] = mapped_column(Boolean, default=False)

    employees: Mapped[List["User"]] = relationship(back_populates="company")
    jobs: Mapped[List["Job"]] = relationship(back_populates="company")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    job_title: Mapped[str] = mapped_column(String, nullable=False)
    job_type: Mapped[str] = mapped_column(String, nullable=False)
    job_site: Mapped[str] = mapped_column(String, nullable=False)
    job_sector: Mapped[str] = mapped_column(String, nullable=False)
    education_qualification: Mapped[str] = mapped_column(String, nullable=False)
    experience_level: Mapped[str] = mapped_column(String, nullable=False)
    gender_preference: Mapped[Optional[str]] = mapped_column(String)
    job_deadline: Mapped[date] = mapped_column(Date, nullable=False)
    job_vacancies: Mapped[Optional[int]] = mapped_column(SmallInteger)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    job_requirements: Mapped[str] = mapped_column(Text)
    job_city: Mapped[str] = mapped_column(String, nullable=False)
    job_country: Mapped[str] = mapped_column(String, nullable=False)
    salary_type: Mapped[Optional[str]] = mapped_column(String)
    salary_currency: Mapped[str] = mapped_column(String)
    salary_amount: Mapped[Optional[int]] = mapped_column(Integer)
    salary_range: Mapped[Optional[dict]] = mapped_column(JSONB)
    job_status: Mapped[Optional[str]] = mapped_column(
        String,
        default="pending",
    )
    job_promoted: Mapped[bool] = mapped_column(Boolean, default=False)
    job_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    category: Mapped["Category"] = relationship(back_populates="jobs")
    company: Mapped["Company"] = relationship(back_populates="jobs")
    employer: Mapped["User"] = relationship(back_populates="jobs")
    applications: Mapped[List["Application"]] = relationship(back_populates="job")
    saved_jobs: Mapped[List["SavedJob"]] = relationship(back_populates="job")
    skills: Mapped[List["Skill"]] = relationship(
        secondary="job_skills", back_populates="jobs"
    )


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("jobs.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    cover_letter: Mapped[Optional[str]] = mapped_column(Text)
    resume: Mapped[Optional[str]] = mapped_column(String)
    portfolio: Mapped[Optional[dict]] = mapped_column(JSONB)
    application_note: Mapped[Optional[str]] = mapped_column(String)
    application_status: Mapped[str] = mapped_column(
        String,
        default="applied",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    job: Mapped["Job"] = relationship(back_populates="applications")
    candidate: Mapped["User"] = relationship(back_populates="applications")


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("jobs.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    job: Mapped["Job"] = relationship(back_populates="saved_jobs")
    user: Mapped["User"] = relationship(back_populates="saved_jobs")


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    users: Mapped[List["User"]] = relationship(
        secondary="user_skills", back_populates="skills"
    )
    jobs: Mapped[List["Job"]] = relationship(
        secondary="job_skills", back_populates="skills"
    )


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), primary_key=True)


class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), primary_key=True)
