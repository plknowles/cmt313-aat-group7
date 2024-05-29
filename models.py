from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(10), nullable=False)
    module_cohort = db.Column(db.Text, nullable=False)
    release_date = db.Column(db.DateTime, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    questions = db.relationship('Question', backref='assessment', lazy=True, cascade='all, delete-orphan')
    feedbacks = db.relationship('AssessmentFeedback', backref='assessment', lazy=True, cascade='all, delete-orphan')


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    question = db.Column(db.String(1024), nullable=False)
    text_answer = db.Column(db.String(1024), nullable=True)
    mcq_correct_answer = db.Column(db.String(255), nullable=True)
    mcq_incorrect_answer1 = db.Column(db.String(255), nullable=True)
    mcq_incorrect_answer2 = db.Column(db.String(255), nullable=True)
    mcq_incorrect_answer3 = db.Column(db.String(255), nullable=True)
    explanation = db.Column(db.String(1024), nullable=True)
   

class StudentAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=False, autoincrement=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    student_id = db.Column(db.String(50), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    attempt_number = db.Column(db.Integer, default=1)
    score = db.Column(db.Float, nullable=True)  # Individual score for the question

    gross_marks = db.Column(db.Integer, nullable=True)  # Total number of correct answers
    total_marks_available = db.Column(db.Integer, nullable=True)  # Total questions in the assessment

    question = db.relationship('Question', backref=db.backref('student_answers', lazy=True))
    assessment = db.relationship('Assessment', backref=db.backref('student_attempts', lazy=True))

class AssessmentFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=False)
    student_id = db.Column(db.String(50), nullable=False)  # Adjust type based on your user ID type
    feedback = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

# David's satisfaction system
class TeacherFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teaching_quality = db.Column(db.Integer, nullable=False)
    content_satisfaction = db.Column(db.Integer, nullable=False)
    interaction_engagement = db.Column(db.Integer, nullable=False)
    resource_availability = db.Column(db.Integer, nullable=False)
    preparation = db.Column(db.Integer, nullable=False)
    course_organization = db.Column(db.Integer, nullable=False)
    additional_comments = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
# end