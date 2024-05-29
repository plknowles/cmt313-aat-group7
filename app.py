from flask import Flask, render_template, request, url_for, jsonify, abort, flash, redirect, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db, Assessment, Question, TeacherFeedback, StudentAnswer, AssessmentFeedback
import os
from flask_migrate import Migrate
from sqlalchemy import desc, func
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assessments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'pass'

db.init_app(app)

with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login function if not logged in

migrate = Migrate(app, db)
# Mock database of users
users = {
    'teacher': {'password': '123'},
    'student': {'password': '123'}
}

# User class
class User(UserMixin):
    def __init__(self, username):
        self.id = username

    @property
    def is_teacher(self):
        return self.id == 'teacher'

    @property
    def is_student(self):
        return self.id == 'student'

# User loader
@login_manager.user_loader
def user_loader(username):
    if username not in users:
        return
    return User(username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)  # Correct instantiation
            login_user(user)
            if username == 'teacher':
                return redirect(url_for('home'))  # Redirect to the 'home' route for teachers
            else:
                return redirect(url_for('home'))  # Redirect to the 'home' route for students
        else:
            flash('Invalid username or password')
    return render_template('login.html')
  
@app.route('/student/attempt_assessment/<int:id>', methods=['GET', 'POST'])
@login_required
def attempt_assessment(id):
    assessment = Assessment.query.get_or_404(id)
    if request.method == 'POST':
        pass
    questions = assessment.questions
    for question in questions:
        if question.type == 'MCQ':
            options = [
                question.mcq_correct_answer,
                question.mcq_incorrect_answer1,
                question.mcq_incorrect_answer2,
                question.mcq_incorrect_answer3
            ]
            random.shuffle(options)  # Shuffle the options
            question.options = options  # Assign the shuffled options to a new attribute for rendering

    return render_template('attempt_assessment.html', assessment=assessment, questions=questions)

@app.route('/assessment_results_single/<int:assessment_id>', methods=['GET'])
@login_required
def assessment_results_single(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    student_answers = (
        StudentAnswer.query
        .filter_by(student_id=current_user.id, assessment_id=assessment_id)
        .order_by(StudentAnswer.attempt_number)
        .all()
    )

    if assessment.type == 'Summative' and datetime.now() < assessment.due_date:
        return render_template('results_not_available.html', message="Assessment results are not available yet.")

    attempt_results = []
    current_attempt_number = None
    attempt_answers = []
    for answer in student_answers:
        if answer.attempt_number != current_attempt_number:
            if attempt_answers:
                max_gross_marks = max(ans.gross_marks for ans in attempt_answers)
                total_marks_available = attempt_answers[0].total_marks_available
                attempt_result = {
                    'attempt_number': current_attempt_number,
                    'answers': attempt_answers,
                    'max_gross_marks': max_gross_marks,
                    'total_marks_available': total_marks_available
                }
                attempt_results.append(attempt_result)
            current_attempt_number = answer.attempt_number
            attempt_answers = []
        attempt_answers.append(answer)

    if attempt_answers:
        max_gross_marks = max(ans.gross_marks for ans in attempt_answers)
        total_marks_available = attempt_answers[0].total_marks_available
        attempt_result = {
            'attempt_number': current_attempt_number,
            'answers': attempt_answers,
            'max_gross_marks': max_gross_marks,
            'total_marks_available': total_marks_available
        }
        attempt_results.append(attempt_result)

    return render_template('assessment_results_single.html', assessment=assessment, attempt_results=attempt_results)

@app.route('/submit_assessment_answers/<int:assessment_id>', methods=['POST'])
@login_required
def submit_assessment_answers(assessment_id):
    assessment = Assessment.query.get_or_404(assessment_id)
    student_id = current_user.id
    last_attempt = db.session.query(db.func.max(StudentAnswer.attempt_number)).filter_by(student_id=student_id, assessment_id=assessment_id).scalar() or 0
    attempt_number = last_attempt + 1

    total_questions = len(assessment.questions)
    correct_answers = 0

    student_answers = []
    for question in assessment.questions:
        answer_input = f'answer_{question.id}'
        student_answer_text = request.form.get(answer_input)
        is_correct = evaluate_answer(question, student_answer_text) if student_answer_text else False
        if is_correct:
            correct_answers += 1
        
        new_student_answer = StudentAnswer(
            assessment_id=assessment.id,
            question_id=question.id,
            student_id=student_id,
            answer=student_answer_text,
            is_correct=is_correct,
            attempt_number=attempt_number,
            score=1 if is_correct else 0,
            total_marks_available=total_questions,
            gross_marks=correct_answers
        )
        student_answers.append(new_student_answer)

    db.session.add_all(student_answers)
    db.session.commit()

    # Calculate max_gross_marks before the redirect
    max_gross_marks = max(answer.gross_marks for answer in student_answers) if student_answers else 0
    
    # Redirect with max_gross_marks passed as a query parameter
    return redirect(url_for('assessment_results_single', assessment_id=assessment_id, max_gross_marks=max_gross_marks))

def evaluate_answer(question, student_answer):
    if question.type == 'MCQ':
        return student_answer == question.mcq_correct_answer
    else:
        return student_answer.strip().lower() == question.text_answer.strip().lower()

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))
from flask_login import current_user

@app.route('/')
@login_required
def home():
    if current_user.is_teacher:
        assessments = Assessment.query.all()
        return render_template('assessment_centre.html', assessments=assessments)
    else:
        assessments = Assessment.query.filter(Assessment.release_date <= datetime.now()).all()

        assessment_data = {}
        for assessment in assessments:
            student_answers = StudentAnswer.query.filter_by(student_id=current_user.id, assessment_id=assessment.id).all()
            if student_answers:
                # Calculate max_gross_marks from the student's attempts
                max_gross_marks = max(answer.gross_marks for answer in student_answers)
                total_questions = len(assessment.questions)
                assessment_data[assessment.id] = {
                    'max_gross_marks': max_gross_marks,
                    'total_questions': total_questions,
                    'score': student_answers[-1].score  # Latest attempt score
                }
            else:
                assessment_data[assessment.id] = {
                    'max_gross_marks': None,
                    'total_questions': len(assessment.questions),
                    'score': None
                }

        current_date = datetime.now()
        return render_template('student_assessment_centre.html', assessments=assessments, assessment_data=assessment_data, current_date=current_date)

# David's satisfaction system
@app.route('/Comments')
@login_required
def Comments():
    return render_template('Comments.html')

@app.route('/teacher_statistics')
@login_required
def teacher_statistics():
    if current_user.id != 'teacher':
        abort(403)  # Forbidden if not a teacher

    assessments = Assessment.query.all()
    student_answers = StudentAnswer.query.all()

    assessment_data = {}
    for assessment in assessments:
        student_scores = [answer.score for answer in student_answers if answer.assessment_id == assessment.id]
        if student_scores:
            class_average = sum(student_scores) / len(student_scores)
            max_score = max(student_scores)
            min_score = min(student_scores)
        else:
            class_average = 0
            max_score = 0
            min_score = 0

        assessment_data[assessment.name] = {
            'class_average': class_average,
            'max_score': max_score,
            'min_score': min_score
        }

    return render_template('teacher_statistics.html', assessment_data=assessment_data)

@app.route('/Satisfaction')
@login_required
def Satisfaction():
    return render_template('Satisfaction.html')

from sqlalchemy.exc import IntegrityError

@app.route('/submit_feedback', methods=['POST'])
@login_required
def submit_feedback():
    try:
        teaching_quality = int(request.form['teachingQuality'])
        content_satisfaction = int(request.form['contentSatisfaction'])
        interaction_engagement = int(request.form['interactiveEngagement'])
        resource_availability = int(request.form['resourceAvailability'])
        preparation = int(request.form['preparation'])
        course_organization = int(request.form['courseOrganization'])
        additional_comments = request.form.get('additionalComments', '')

        feedback = TeacherFeedback(
            teaching_quality=teaching_quality,
            content_satisfaction=content_satisfaction,
            interaction_engagement=interaction_engagement,
            resource_availability=resource_availability,
            preparation=preparation,
            course_organization=course_organization,
            additional_comments=additional_comments
        )

        db.session.add(feedback)
        db.session.commit()

        return redirect(url_for('Thankyou'))
    except IntegrityError as e:
        db.session.rollback()
        print("Error:", e)
        flash('An error occurred while saving data, please try again.')
        return redirect(url_for('Satisfaction'))
    except ValueError as e:
        print("Conversion Error:", e)
        flash('Data type error in submission, please ensure the input is correct.')
        return redirect(url_for('Satisfaction'))

@app.route('/Thankyou')
@login_required
def Thankyou():
    return render_template('Thankyou.html')

@app.route('/teacher_feedback')
def teacher_feedback():
    teacher_feedback_data = TeacherFeedback.query.all()
    assessment_feedback_data = AssessmentFeedback.query.join(Assessment).all()
    return render_template('teacher_feedback.html', teacher_feedback_data=teacher_feedback_data, assessment_feedback_data=assessment_feedback_data)
# David's job end

@app.route('/assessment_centre')
@login_required
def assessment_centre():
    if current_user.is_teacher:
        assessments = Assessment.query.all()
    else:
        assessments = Assessment.query.filter(
            Assessment.release_date <= datetime.now()
        ).all()

    student_marks = {}
    total_marks = {}
    for assessment in assessments:
        total_marks[assessment.id] = sum(1 for question in assessment.questions if question.text_answer)
        student_answer = StudentAnswer.query.filter_by(
            student_id=current_user.id, assessment_id=assessment.id
        ).order_by(StudentAnswer.attempt_number.desc()).first()
        student_marks[assessment.id] = student_answer.score if student_answer else None

    current_date = datetime.now()
    return render_template('assessment_centre.html', assessments=assessments,
                           student_marks=student_marks, total_marks=total_marks, current_date=current_date)

@app.route('/create_assessment', methods=['GET', 'POST'])
@login_required
def create_assessment():
    return render_template('create_assessment.html')

@app.route('/submit_assessment', methods=['POST'])
@login_required
def submit_assessment():
    try:
        assessment_name = request.form['assessment_name']
        assessment_type = request.form['assessment_type']
        difficulty = request.form['difficulty']
        module_cohort = request.form['module_cohort']
        release_date = datetime.strptime(request.form['release_date'], '%Y-%m-%dT%H:%M')
        due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%dT%H:%M')
        
        new_assessment = Assessment(
            name=assessment_name, 
            type=assessment_type, 
            difficulty=difficulty, 
            module_cohort=module_cohort, 
            release_date=release_date, 
            due_date=due_date
        )
        db.session.add(new_assessment)
        db.session.flush()  # Necessary to get the assessment ID
        
        question_keys = [key for key in request.form if key.startswith("mc_question_") or key.startswith("text_question_")]
        for key in question_keys:
            question_type = 'MCQ' if 'mc_question' in key else 'Text'
            question_text = request.form[key]
            explanation = request.form.get(key.replace("question", "explanation"), '')
            if question_type == 'MCQ':
                mcq_correct_answer = request.form.get(key.replace("question", "correct_answer"))
                mcq_incorrect_answers = [
                    request.form.get(key.replace("question", "incorrect_answer1")),
                    request.form.get(key.replace("question", "incorrect_answer2")),
                    request.form.get(key.replace("question", "incorrect_answer3"))
                ]
                new_question = Question(
                    assessment_id=new_assessment.id,
                    type=question_type,
                    question=question_text,
                    mcq_correct_answer=mcq_correct_answer,
                    mcq_incorrect_answer1=mcq_incorrect_answers[0],
                    mcq_incorrect_answer2=mcq_incorrect_answers[1],
                    mcq_incorrect_answer3=mcq_incorrect_answers[2], 
                    explanation=explanation
                )
            else:  # Text Question
                text_answer = request.form.get(key.replace("question", "answer"))
                new_question = Question(
                    assessment_id=new_assessment.id,
                    type=question_type,
                    question=question_text,
                    text_answer=text_answer, 
                    explanation=explanation
                )
            db.session.add(new_question)

        db.session.commit()

        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", 'error')
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/edit_assessment/<int:id>', methods=['GET'])
@login_required
def edit_assessment(id):
    assessment = Assessment.query.get_or_404(id)
    questions = assessment.questions
    return render_template('edit_assessment.html', assessment=assessment, questions=questions)

@app.route('/update_assessment/<int:id>', methods=['POST'])
@login_required
def update_assessment(id):
    try:
        assessment = db.session.get(Assessment, id)
        if not assessment:
            flash('Error: Assessment not found', 'error')
            return jsonify({'success': False, 'message': 'Assessment not found'}), 404
        
        # Update assessment details
        assessment.name = request.form['assessment_name']
        assessment.type = request.form['assessment_type']
        assessment.difficulty = request.form['difficulty']
        assessment.module_cohort = request.form['module_cohort']
        assessment.release_date = datetime.strptime(request.form['release_date'], '%Y-%m-%dT%H:%M')
        assessment.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%dT%H:%M')

        # Update existing questions
        for question in assessment.questions:
            question_text_key = f'question_text_{question.id}'
            explanation_key = f'explanation_{question.id}'
            if question_text_key in request.form:
                question.question = request.form[question_text_key]
                question.explanation = request.form.get(explanation_key, '')
                if question.type == 'MCQ':
                    question.mcq_correct_answer = request.form[f'mcq_correct_answer_{question.id}']
                    question.mcq_incorrect_answer1 = request.form[f'mcq_incorrect_answer1_{question.id}']
                    question.mcq_incorrect_answer2 = request.form[f'mcq_incorrect_answer2_{question.id}']
                    question.mcq_incorrect_answer3 = request.form[f'mcq_incorrect_answer3_{question.id}']
                else:
                    text_answer_key = f'text_answer_{question.id}'
                    question.text_answer = request.form.get(text_answer_key)

        # Handle deleted questions
        deleted_questions = request.form.get('deleted_questions', '')
        if deleted_questions:
            delete_question_ids = [int(qid) for qid in deleted_questions.split(',') if qid.isdigit()]
            for question_id in delete_question_ids:
                question = db.session.get(Question, question_id)
                if question:
                    db.session.delete(question)

        # Add new questions
        new_question_keys = [key for key in request.form if key.startswith("mc_question_") or key.startswith("text_question_")]
        for key in new_question_keys:
            question_type = 'MCQ' if 'mc_question' in key else 'Text'
            question_text = request.form[key]
            new_question = Question(
                assessment_id=assessment.id,
                type=question_type,
                question=question_text,
                text_answer=request.form.get(key.replace("question", "answer")) if question_type == 'Text' else None,
                mcq_correct_answer=request.form.get(key.replace("question", "correct_answer")) if question_type == 'MCQ' else None,
                mcq_incorrect_answer1=request.form.get(key.replace("question", "incorrect_answer1")) if question_type == 'MCQ' else None,
                mcq_incorrect_answer2=request.form.get(key.replace("question", "incorrect_answer2")) if question_type == 'MCQ' else None,
                mcq_incorrect_answer3=request.form.get(key.replace("question", "incorrect_answer3")) if question_type == 'MCQ' else None,
            )
            db.session.add(new_question)

        # Commit changes
        db.session.commit()
        flash('Assessment updated successfully!', 'success')
        return jsonify({'success': True}), 200

    except Exception as e:
        db.session.rollback()
        flash(f"Error updating assessment: {str(e)}", 'error')
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/delete_assessment/<int:id>', methods=['POST'])
@login_required
def delete_assessment(id):
    assessment = Assessment.query.get_or_404(id)

    # Delete associated student answers
    StudentAnswer.query.filter_by(assessment_id=id).delete()
    AssessmentFeedback.query.filter_by(assessment_id=id).delete()
    # Delete associated questions
    Question.query.filter_by(assessment_id=id).delete()

    # delete the assessment itself
    db.session.delete(assessment)
    db.session.commit()
    flash('Assessment and all related questions and answers deleted successfully', 'info')
    return redirect(url_for('home'))

@app.route('/send_assessment_feedback/<int:id>', methods=['GET'])
@login_required
def send_assessment_feedback(id):
    assessment = Assessment.query.get_or_404(id)
    return render_template('send_assessment_feedback.html', assessment=assessment)

@app.route('/submit_assessment_feedback/<int:id>', methods=['POST'])
@login_required
def submit_assessment_feedback(id):
    feedback_text = request.form['feedback']
    student_id = current_user.id  # Assuming you have access to the current user's id
    try:
        feedback = AssessmentFeedback(
            assessment_id=id,
            student_id=student_id,
            feedback=feedback_text
        )
        db.session.add(feedback)
        db.session.commit()
        flash('Feedback submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting feedback: {str(e)}', 'error')

    return redirect(url_for('home'))

# put at bottom
if __name__ == "__main__":
    app.run(debug=True)