from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, CheckConstraint
from sqlalchemy.sql import func
from app.db.session import Base


class Score(Base):
    __tablename__ = "scores"
    __table_args__ = (
        CheckConstraint("quiz1_marks BETWEEN 0 AND 10",    name="chk_quiz1"),
        CheckConstraint("quiz2_marks BETWEEN 0 AND 10",    name="chk_quiz2"),
        CheckConstraint("quiz3_marks BETWEEN 0 AND 10",    name="chk_quiz3"),
        CheckConstraint("midterm_marks BETWEEN 0 AND 30",  name="chk_midterm"),
        CheckConstraint("final_marks BETWEEN 0 AND 50",    name="chk_final"),
    )

    id              = Column(Integer, primary_key=True, autoincrement=True)
    student_id      = Column(Integer, index=True, nullable=False)
    name            = Column(String(100), nullable=True)
    age             = Column(Integer, nullable=True)
    gender          = Column(String(10), nullable=True)

    # Raw marks (as per CSV)
    quiz1_marks     = Column(Float, nullable=False)   # /10
    quiz2_marks     = Column(Float, nullable=False)   # /10
    quiz3_marks     = Column(Float, nullable=False)   # /10
    midterm_marks   = Column(Float, nullable=False)   # /30
    final_marks     = Column(Float, nullable=False)   # /50
    previous_gpa    = Column(Float, nullable=True)
    lectures_attended = Column(Integer, nullable=True, default=0)
    labs_attended   = Column(Integer, nullable=True, default=0)

    # Computed fields
    quiz_score      = Column(Float, nullable=True)   # /20
    midterm_score   = Column(Float, nullable=True)   # /30
    final_score     = Column(Float, nullable=True)   # /50
    total_score     = Column(Float, nullable=True)   # /100
    grade           = Column(String(2), nullable=True)
    grade_point     = Column(Float, nullable=True)
    pass_fail       = Column(String(4), nullable=True)   # PASS / FAIL
    is_pass         = Column(Boolean, nullable=True)
    performance_tier = Column(String(20), nullable=True)
    attendance_rate = Column(Float, nullable=True)

    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted      = Column(Boolean, default=False)

    def compute_scores(self):
        """Compute all derived score fields in place."""
        # Weighted scores
        self.quiz_score     = round((self.quiz1_marks + self.quiz2_marks + self.quiz3_marks) / 3 / 10 * 20, 2)
        self.midterm_score  = round(self.midterm_marks / 30 * 30, 2)
        self.final_score    = round(self.final_marks   / 50 * 50, 2)
        self.total_score    = round(self.quiz_score + self.midterm_score + self.final_score, 2)

        # Pass / Fail  ← threshold = 50.0
        self.is_pass  = self.total_score >= 50.0
        self.pass_fail = "PASS" if self.is_pass else "FAIL"

        # Grade
        t = self.total_score
        if   t >= 85: self.grade, self.grade_point = "A", 4.0
        elif t >= 70: self.grade, self.grade_point = "B", 3.0
        elif t >= 55: self.grade, self.grade_point = "C", 2.0
        elif t >= 50: self.grade, self.grade_point = "D", 1.0
        else:         self.grade, self.grade_point = "F", 0.0

        # Performance tier
        if   t >= 85: self.performance_tier = "Excellent"
        elif t >= 70: self.performance_tier = "Good"
        elif t >= 55: self.performance_tier = "Average"
        elif t >= 50: self.performance_tier = "Below Average"
        else:         self.performance_tier = "Fail"

        # Attendance rate (max 12 lectures + 6 labs = 18)
        lec = self.lectures_attended or 0
        lab = self.labs_attended or 0
        self.attendance_rate = round((lec + lab) / 18.0, 3)

        return self
