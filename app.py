import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload

# Allowed poster extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home Page
@app.route('/')
def index():
    return render_template('index.html')

# ---------------- COLLEGE ROUTES ----------------
@app.route('/college/signup', methods=['GET', 'POST'])
def college_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        address = request.form['address']
        password = request.form['password']
        # Check if college exists
        exists = supabase.table('colleges').select('name').eq('name', name).execute().data
        if exists:
            flash('College name already exists!', 'danger')
            return redirect(url_for('college_signup'))
        supabase.table('colleges').insert({
            'name': name,
            'email': email,
            'address': address,
            'password': password
        }).execute()
        flash('Signup successful! Please login.', 'success')
        return redirect(url_for('college_login'))
    return render_template('college_signup.html')

@app.route('/college/login', methods=['GET', 'POST'])
def college_login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        result = supabase.table('colleges').select('*').eq('name', name).eq('password', password).execute()
        colleges = result.data
        if colleges and len(colleges) > 0:
            college = colleges[0]
            session['college_id'] = college['college_id']
            session['college_name'] = college['name']
            return redirect(url_for('college_dashboard'))
        flash('Invalid credentials!', 'danger')
    return render_template('college_login.html')

@app.route('/college/dashboard', methods=['GET', 'POST'])
def college_dashboard():
    if 'college_id' not in session:
        return redirect(url_for('college_login'))
    college_id = session['college_id']
    # Post Hackathon
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        post_date = datetime.now().date().isoformat()
        deadline = request.form['deadline']
        prizes = request.form.get('prizes', '')
        poster_url = None
        file = request.files.get('poster')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_bytes = file.read()
            supa_path = f"{college_id}/{filename}"
            try:
                res = supabase.storage.from_('hackathon-posters').upload(
                    supa_path,
                    file_bytes,
                    {"content-type": file.content_type, "upsert": "true"}
                )
                poster_url = supabase.storage.from_('hackathon-posters').get_public_url(supa_path)
            except Exception as e:
                flash('Poster upload failed: ' + str(e), 'danger')
        supabase.table('hackathons').insert({
            'title': title,
            'description': description,
            'post_date': post_date,
            'deadline': deadline,
            'prizes': prizes,
            'poster_url': poster_url,
            'college_id': college_id
        }).execute()
        flash('Hackathon posted!', 'success')
        return redirect(url_for('college_dashboard'))
    # View hackathons
    hackathons = supabase.table('hackathons').select('*').eq('college_id', college_id).order('post_date', desc=True).execute().data
    # View judges
    judges = supabase.table('judges').select('*').eq('college_id', college_id).execute().data
    # View student ideas
    ideas = supabase.table('ideas').select('*, students(*), hackathons(title)').execute().data
    # Only show ideas for this college's hackathons
    college_hackathon_ids = [h['hackathon_id'] for h in hackathons]
    ideas = [i for i in ideas if i['hackathon_id'] in college_hackathon_ids]
    # Fetch college details
    college = supabase.table('colleges').select('*').eq('college_id', college_id).single().execute().data
    return render_template('college_dashboard.html', hackathons=hackathons, judges=judges, ideas=ideas, college=college)

@app.route('/college/judge', methods=['POST'])
def add_judge():
    if 'college_id' not in session:
        return redirect(url_for('college_login'))
    judge_id = request.form['judge_id']
    name = request.form['name']
    password = request.form['password']
    college_id = session['college_id']
    exists = supabase.table('judges').select('judge_id').eq('judge_id', judge_id).execute().data
    if exists:
        flash('Judge ID already exists!', 'danger')
    else:
        supabase.table('judges').insert({
            'judge_id': judge_id,
            'name': name,
            'password': password,
            'college_id': college_id
        }).execute()
        flash('Judge added!', 'success')
    return redirect(url_for('college_dashboard'))

@app.route('/college/logout')
def college_logout():
    session.clear()
    return redirect(url_for('index'))

# ---------------- STUDENT ROUTES ----------------
@app.route('/student/signup', methods=['GET', 'POST'])
def student_signup():
    colleges = supabase.table('colleges').select('college_id, name').execute().data
    if request.method == 'POST':
        name = request.form['name']
        roll_no = request.form['roll_no']
        password = request.form['password']
        year = request.form['year']
        branch = request.form['branch']
        college_id = request.form['college_id']
        exists = supabase.table('students').select('roll_no').eq('roll_no', roll_no).execute().data
        if exists:
            flash('Roll number already exists!', 'danger')
            return redirect(url_for('student_signup'))
        supabase.table('students').insert({
            'name': name,
            'roll_no': roll_no,
            'password': password,
            'year': year,
            'branch': branch,
            'college_id': college_id
        }).execute()
        flash('Signup successful! Please login.', 'success')
        return redirect(url_for('student_login'))
    return render_template('student_signup.html', colleges=colleges)

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        password = request.form['password']
        result = supabase.table('students').select('*').eq('roll_no', roll_no).eq('password', password).execute()
        students = result.data
        print("LOGIN QUERY RESULT:", students)
        if students and len(students) > 0:
            student = students[0]
            session['student_id'] = student['student_id']
            session['student_name'] = student['name']
            session['college_id'] = student['college_id']
            return redirect(url_for('student_dashboard'))
        flash('Invalid credentials!', 'danger')
    return render_template('student_login.html')

@app.route('/student/dashboard', methods=['GET', 'POST'])
def student_dashboard():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    student_id = session['student_id']
    college_id = session['college_id']
    # View hackathons
    hackathons = supabase.table('hackathons').select('*').eq('college_id', college_id).order('post_date', desc=True).execute().data
    # Submit idea
    if request.method == 'POST':
        hackathon_id = request.form['hackathon_id']
        title = request.form['title']
        description = request.form['description']
        prototype = request.form.get('prototype', '')
        supabase.table('ideas').insert({
            'student_id': student_id,
            'hackathon_id': hackathon_id,
            'title': title,
            'description': description,
            'prototype': prototype
        }).execute()
        flash('Idea submitted!', 'success')
        return redirect(url_for('student_dashboard'))
    # View submitted ideas
    ideas = supabase.table('ideas').select('*, hackathons(title), scores(score, judge_id)').eq('student_id', student_id).execute().data
    # Fetch student details
    student = supabase.table('students').select('*').eq('student_id', student_id).single().execute().data
    return render_template('student_dashboard.html', hackathons=hackathons, ideas=ideas, student=student)

@app.route('/student/logout')
def student_logout():
    session.clear()
    return redirect(url_for('index'))

# ---------------- JUDGE ROUTES ----------------
@app.route('/judge/login', methods=['GET', 'POST'])
def judge_login():
    if request.method == 'POST':
        judge_id = request.form['judge_id']
        password = request.form['password']
        result = supabase.table('judges').select('*').eq('judge_id', judge_id).eq('password', password).execute()
        judges = result.data
        if judges and len(judges) > 0:
            judge = judges[0]
            session['judge_id'] = judge['judge_id']
            session['college_id'] = judge['college_id']
            return redirect(url_for('judge_dashboard'))
        flash('Invalid credentials!', 'danger')
    return render_template('judge_login.html')

@app.route('/judge/dashboard', methods=['GET', 'POST'])
def judge_dashboard():
    if 'judge_id' not in session:
        return redirect(url_for('judge_login'))
    judge_id = session['judge_id']
    college_id = session['college_id']
    # Get hackathons for this college
    hackathons = supabase.table('hackathons').select('hackathon_id, title').eq('college_id', college_id).execute().data
    hackathon_ids = [h['hackathon_id'] for h in hackathons]
    # Get ideas for these hackathons
    ideas = supabase.table('ideas').select('*, students(*), hackathons(title), scores(score, judge_id)').in_('hackathon_id', hackathon_ids).execute().data
    # Handle scoring
    if request.method == 'POST':
        idea_id = request.form['idea_id']
        score = int(request.form['score'])
        # Upsert score
        existing = supabase.table('scores').select('score_id').eq('idea_id', idea_id).eq('judge_id', judge_id).execute().data
        if existing:
            supabase.table('scores').update({'score': score}).eq('score_id', existing[0]['score_id']).execute()
        else:
            supabase.table('scores').insert({'idea_id': idea_id, 'judge_id': judge_id, 'score': score}).execute()
        flash('Score submitted!', 'success')
        return redirect(url_for('judge_dashboard'))
    return render_template('judge_dashboard.html', ideas=ideas)

@app.route('/judge/logout')
def judge_logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 