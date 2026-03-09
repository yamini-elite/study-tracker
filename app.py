"""
Study Tracker Web Application - Flask Backend
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, random
from datetime import datetime, date, timedelta

app = Flask(__name__)
app.secret_key = 'studytracker_secret_key_2024'
DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
        subjects TEXT DEFAULT '', study_goal INTEGER DEFAULT 4,
        theme TEXT DEFAULT 'dark', color_theme TEXT DEFAULT 'purple',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        task_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, task_name TEXT NOT NULL, subject TEXT DEFAULT '',
        status TEXT DEFAULT 'pending', priority TEXT DEFAULT 'medium',
        date TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, subject TEXT NOT NULL,
        start_time TEXT NOT NULL, end_time TEXT NOT NULL,
        day TEXT NOT NULL, color TEXT DEFAULT '#7c3aed',
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, message TEXT NOT NULL,
        reminder_time TEXT NOT NULL, reminder_date TEXT NOT NULL,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS streaks (
        user_id INTEGER PRIMARY KEY, current_streak INTEGER DEFAULT 0,
        longest_streak INTEGER DEFAULT 0, last_active_date TEXT,
        total_days INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, subject TEXT DEFAULT 'General',
        duration INTEGER DEFAULT 0, session_date TEXT NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS study_groups (
        group_id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT NOT NULL, description TEXT DEFAULT '',
        creator_id INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(creator_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS group_members (
        group_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(group_id, user_id),
        FOREIGN KEY(group_id) REFERENCES study_groups(group_id),
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS group_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
        message TEXT NOT NULL, sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(group_id) REFERENCES study_groups(group_id),
        FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

def update_streak(user_id):
    conn = get_db()
    streak = conn.execute('SELECT * FROM streaks WHERE user_id=?', (user_id,)).fetchone()
    today = str(date.today())
    yesterday = str(date.today() - timedelta(days=1))
    if streak:
        last = streak['last_active_date']
        if last == today:
            conn.close(); return
        elif last == yesterday:
            new_streak = streak['current_streak'] + 1
            longest = max(new_streak, streak['longest_streak'])
        else:
            new_streak = 1
            longest = streak['longest_streak']
        conn.execute('UPDATE streaks SET current_streak=?,longest_streak=?,last_active_date=?,total_days=total_days+1 WHERE user_id=?',
                     (new_streak, longest, today, user_id))
    else:
        conn.execute('INSERT INTO streaks VALUES (?,1,1,?,1)', (user_id, today))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return redirect(url_for('dashboard') if 'user_id' in session else url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        name, email, password = data.get('name','').strip(), data.get('email','').strip(), data.get('password','')
        if not all([name, email, password]):
            return jsonify({'success':False,'message':'All fields required'})
        conn = get_db()
        if conn.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone():
            conn.close(); return jsonify({'success':False,'message':'Email already registered'})
        conn.execute('INSERT INTO users (name,email,password,subjects,study_goal) VALUES (?,?,?,?,?)',
                     (name, email, generate_password_hash(password), data.get('subjects',''), data.get('study_goal',4)))
        conn.commit()
        uid = conn.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone()['id']
        conn.execute('INSERT INTO streaks (user_id,current_streak,last_active_date) VALUES (?,0,?)',(uid, str(date.today())))
        conn.commit(); conn.close()
        return jsonify({'success':True})
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email=?',(data.get('email',''),)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], data.get('password','')):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            update_streak(user['id'])
            return jsonify({'success':True})
        return jsonify({'success':False,'message':'Invalid credentials'})
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    return redirect(url_for('login')) if 'user_id' not in session else render_template('dashboard.html')

@app.route('/api/dashboard')
def api_dashboard():
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    uid = session['user_id']
    today = str(date.today())
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id=? AND date=?',(uid,today)).fetchall()
    streak = conn.execute('SELECT * FROM streaks WHERE user_id=?',(uid,)).fetchone()
    reminder = conn.execute('SELECT * FROM reminders WHERE user_id=? AND reminder_date=? AND is_active=1 ORDER BY reminder_time LIMIT 1',(uid,today)).fetchone()
    conn.close()
    quotes = ["Success is the sum of small efforts repeated daily.","The secret of getting ahead is getting started.",
              "Don't watch the clock; do what it does. Keep going.","Push yourself, because no one else is going to do it for you.",
              "The beautiful thing about learning is nobody can take it away from you.","Study hard, for the well is deep, and our brains are shallow.",
              "Education is the passport to the future.","Believe you can and you're halfway there."]
    return jsonify({
        'user': dict(user), 'tasks': [dict(t) for t in tasks],
        'streak': dict(streak) if streak else {'current_streak':0,'longest_streak':0},
        'upcoming_reminder': dict(reminder) if reminder else None,
        'progress': {'total':len(tasks),'done':sum(1 for t in tasks if t['status']=='completed')},
        'quote': quotes[date.today().timetuple().tm_yday % len(quotes)], 'today': today})

@app.route('/checklist')
def checklist():
    return redirect(url_for('login')) if 'user_id' not in session else render_template('checklist.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    fd = request.args.get('date', str(date.today()))
    conn = get_db()
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id=? AND date=? ORDER BY created_at DESC',(session['user_id'],fd)).fetchall()
    conn.close(); return jsonify([dict(t) for t in tasks])

@app.route('/api/tasks', methods=['POST'])
def add_task():
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    data = request.get_json()
    conn = get_db()
    conn.execute('INSERT INTO tasks (user_id,task_name,subject,priority,date) VALUES (?,?,?,?,?)',
                 (session['user_id'],data['task_name'],data.get('subject',''),data.get('priority','medium'),data.get('date',str(date.today()))))
    conn.commit()
    tid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    task = conn.execute('SELECT * FROM tasks WHERE task_id=?',(tid,)).fetchone()
    conn.close(); return jsonify(dict(task))

@app.route('/api/tasks/<int:tid>', methods=['PUT'])
def update_task(tid):
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    data = request.get_json()
    conn = get_db()
    if 'status' in data:
        conn.execute('UPDATE tasks SET status=? WHERE task_id=? AND user_id=?',(data['status'],tid,session['user_id']))
    if 'task_name' in data:
        conn.execute('UPDATE tasks SET task_name=?,subject=?,priority=? WHERE task_id=? AND user_id=?',
                     (data['task_name'],data.get('subject',''),data.get('priority','medium'),tid,session['user_id']))
    conn.commit()
    task = conn.execute('SELECT * FROM tasks WHERE task_id=?',(tid,)).fetchone()
    conn.close(); return jsonify(dict(task))

@app.route('/api/tasks/<int:tid>', methods=['DELETE'])
def delete_task(tid):
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    conn = get_db()
    conn.execute('DELETE FROM tasks WHERE task_id=? AND user_id=?',(tid,session['user_id']))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/timetable')
def timetable():
    return redirect(url_for('login')) if 'user_id' not in session else render_template('timetable.html')

@app.route('/api/timetable', methods=['GET'])
def get_timetable():
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    conn = get_db()
    entries = conn.execute('SELECT * FROM timetable WHERE user_id=? ORDER BY day,start_time',(session['user_id'],)).fetchall()
    conn.close(); return jsonify([dict(e) for e in entries])

@app.route('/api/timetable', methods=['POST'])
def add_timetable():
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    data = request.get_json()
    color = random.choice(['#7c3aed','#2563eb','#059669','#d97706','#dc2626','#db2777','#0891b2'])
    conn = get_db()
    conn.execute('INSERT INTO timetable (user_id,subject,start_time,end_time,day,color) VALUES (?,?,?,?,?,?)',
                 (session['user_id'],data['subject'],data['start_time'],data['end_time'],data['day'],color))
    conn.commit()
    eid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    entry = conn.execute('SELECT * FROM timetable WHERE id=?',(eid,)).fetchone()
    conn.close(); return jsonify(dict(entry))

@app.route('/api/timetable/<int:eid>', methods=['PUT'])
def update_timetable(eid):
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    data = request.get_json()
    conn = get_db()
    conn.execute('UPDATE timetable SET subject=?,start_time=?,end_time=?,day=? WHERE id=? AND user_id=?',
                 (data['subject'],data['start_time'],data['end_time'],data['day'],eid,session['user_id']))
    conn.commit()
    entry = conn.execute('SELECT * FROM timetable WHERE id=?',(eid,)).fetchone()
    conn.close(); return jsonify(dict(entry))

@app.route('/api/timetable/<int:eid>', methods=['DELETE'])
def delete_timetable(eid):
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    conn = get_db()
    conn.execute('DELETE FROM timetable WHERE id=? AND user_id=?',(eid,session['user_id']))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    conn = get_db()
    reminders = conn.execute('SELECT * FROM reminders WHERE user_id=? ORDER BY reminder_date,reminder_time',(session['user_id'],)).fetchall()
    conn.close(); return jsonify([dict(r) for r in reminders])

@app.route('/api/reminders', methods=['POST'])
def add_reminder():
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    data = request.get_json()
    conn = get_db()
    conn.execute('INSERT INTO reminders (user_id,message,reminder_time,reminder_date) VALUES (?,?,?,?)',
                 (session['user_id'],data['message'],data['time'],data['date']))
    conn.commit()
    rid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    r = conn.execute('SELECT * FROM reminders WHERE id=?',(rid,)).fetchone()
    conn.close(); return jsonify(dict(r))

@app.route('/api/reminders/<int:rid>', methods=['DELETE'])
def delete_reminder(rid):
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    conn = get_db()
    conn.execute('DELETE FROM reminders WHERE id=? AND user_id=?',(rid,session['user_id']))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/analytics')
def analytics():
    return redirect(url_for('login')) if 'user_id' not in session else render_template('analytics.html')

@app.route('/api/analytics')
def api_analytics():
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    uid = session['user_id']
    conn = get_db()
    labels, completed_data, total_data = [], [], []
    for i in range(6,-1,-1):
        d = str(date.today() - timedelta(days=i))
        labels.append(d[5:])
        total_data.append(conn.execute('SELECT COUNT(*) as c FROM tasks WHERE user_id=? AND date=?',(uid,d)).fetchone()['c'])
        completed_data.append(conn.execute("SELECT COUNT(*) as c FROM tasks WHERE user_id=? AND date=? AND status='completed'",(uid,d)).fetchone()['c'])
    subjects = conn.execute("SELECT subject, COUNT(*) as count FROM tasks WHERE user_id=? AND subject!='' GROUP BY subject",(uid,)).fetchall()
    sessions = conn.execute('SELECT session_date, SUM(duration) as total FROM study_sessions WHERE user_id=? GROUP BY session_date ORDER BY session_date DESC LIMIT 7',(uid,)).fetchall()
    streak = conn.execute('SELECT * FROM streaks WHERE user_id=?',(uid,)).fetchone()
    total_tasks = conn.execute('SELECT COUNT(*) as c FROM tasks WHERE user_id=?',(uid,)).fetchone()['c']
    done_tasks = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE user_id=? AND status='completed'",(uid,)).fetchone()['c']
    conn.close()
    return jsonify({
        'weekly':{'labels':labels,'completed':completed_data,'total':total_data},
        'subjects':[{'subject':s['subject'],'count':s['count']} for s in subjects],
        'sessions':[{'date':s['session_date'],'hours':round(s['total']/60,1)} for s in sessions],
        'streak':dict(streak) if streak else {},
        'stats':{'total_tasks':total_tasks,'done_tasks':done_tasks}})

@app.route('/api/study_session', methods=['POST'])
def log_session():
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    data = request.get_json()
    conn = get_db()
    conn.execute('INSERT INTO study_sessions (user_id,subject,duration,session_date) VALUES (?,?,?,?)',
                 (session['user_id'],data.get('subject','General'),data.get('duration',25),str(date.today())))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/collaboration')
def collaboration():
    return redirect(url_for('login')) if 'user_id' not in session else render_template('collaboration.html')

@app.route('/api/groups', methods=['GET'])
def get_groups():
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    uid = session['user_id']
    conn = get_db()
    my_groups = conn.execute('''SELECT g.*, u.name as creator_name,
        (SELECT COUNT(*) FROM group_members WHERE group_id=g.group_id) as member_count
        FROM study_groups g JOIN group_members gm ON g.group_id=gm.group_id
        JOIN users u ON g.creator_id=u.id WHERE gm.user_id=?''',(uid,)).fetchall()
    all_groups = conn.execute('''SELECT g.*, u.name as creator_name,
        (SELECT COUNT(*) FROM group_members WHERE group_id=g.group_id) as member_count
        FROM study_groups g JOIN users u ON g.creator_id=u.id''').fetchall()
    conn.close()
    my_ids = {g['group_id'] for g in my_groups}
    return jsonify({'my_groups':[dict(g) for g in my_groups],
                    'all_groups':[dict(g) for g in all_groups if g['group_id'] not in my_ids]})

@app.route('/api/groups', methods=['POST'])
def create_group():
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    data = request.get_json()
    uid = session['user_id']
    conn = get_db()
    conn.execute('INSERT INTO study_groups (group_name,description,creator_id) VALUES (?,?,?)',
                 (data['group_name'],data.get('description',''),uid))
    conn.commit()
    gid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.execute('INSERT INTO group_members (group_id,user_id) VALUES (?,?)',(gid,uid))
    conn.commit(); conn.close()
    return jsonify({'success':True,'group_id':gid})

@app.route('/api/groups/<int:gid>/join', methods=['POST'])
def join_group(gid):
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    uid = session['user_id']
    conn = get_db()
    if not conn.execute('SELECT * FROM group_members WHERE group_id=? AND user_id=?',(gid,uid)).fetchone():
        conn.execute('INSERT INTO group_members (group_id,user_id) VALUES (?,?)',(gid,uid))
        conn.commit()
    conn.close(); return jsonify({'success':True})

@app.route('/api/groups/<int:gid>/messages', methods=['GET'])
def get_messages(gid):
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    conn = get_db()
    msgs = conn.execute('''SELECT gm.*, u.name as sender_name FROM group_messages gm
        JOIN users u ON gm.user_id=u.id WHERE gm.group_id=? ORDER BY gm.sent_at DESC LIMIT 50''',(gid,)).fetchall()
    conn.close(); return jsonify([dict(m) for m in reversed(msgs)])

@app.route('/api/groups/<int:gid>/messages', methods=['POST'])
def send_message(gid):
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    data = request.get_json()
    conn = get_db()
    conn.execute('INSERT INTO group_messages (group_id,user_id,message) VALUES (?,?,?)',
                 (gid,session['user_id'],data['message']))
    conn.commit(); conn.close(); return jsonify({'success':True})

@app.route('/profile')
def profile():
    return redirect(url_for('login')) if 'user_id' not in session else render_template('profile.html')

@app.route('/api/profile', methods=['GET'])
def get_profile():
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    conn = get_db()
    user = conn.execute('SELECT id,name,email,subjects,study_goal,theme,color_theme,created_at FROM users WHERE id=?',(session['user_id'],)).fetchone()
    streak = conn.execute('SELECT * FROM streaks WHERE user_id=?',(session['user_id'],)).fetchone()
    total = conn.execute('SELECT COUNT(*) as c FROM tasks WHERE user_id=?',(session['user_id'],)).fetchone()['c']
    done = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE user_id=? AND status='completed'",(session['user_id'],)).fetchone()['c']
    conn.close()
    return jsonify({'user':dict(user),'streak':dict(streak) if streak else {},'stats':{'total_tasks':total,'done_tasks':done}})

@app.route('/api/profile', methods=['PUT'])
def update_profile():
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    data = request.get_json()
    conn = get_db()
    conn.execute('UPDATE users SET name=?,subjects=?,study_goal=?,theme=?,color_theme=? WHERE id=?',
                 (data.get('name'),data.get('subjects',''),data.get('study_goal',4),
                  data.get('theme','dark'),data.get('color_theme','purple'),session['user_id']))
    conn.commit(); conn.close()
    session['user_name'] = data.get('name')
    return jsonify({'success':True})

@app.route('/motivation')
def motivation():
    return redirect(url_for('login')) if 'user_id' not in session else render_template('motivation.html')

@app.route('/tips')
def tips():
    return redirect(url_for('login')) if 'user_id' not in session else render_template('tips.html')

@app.route('/chatbot')
def chatbot():
    return redirect(url_for('login')) if 'user_id' not in session else render_template('chatbot.html')

@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    msg = request.get_json().get('message','').lower()
    responses = {
        'pomodoro': "🍅 Pomodoro Technique: Study for 25 minutes, then take a 5-minute break. After 4 sessions, take a 15-30 minute break. Perfect for maintaining deep focus!",
        'focus': "🎯 To improve focus: eliminate phone distractions, use the Pomodoro technique, keep your workspace clean, and study during your peak energy hours.",
        'memory': "🧠 Better memory: use active recall (test yourself), spaced repetition (review at intervals of 1, 3, 7, 14 days), and teach concepts to others.",
        'motivation': "💪 Stay motivated by setting small achievable goals, tracking your daily streak, rewarding yourself for milestones, and connecting study to your bigger dreams!",
        'schedule': "📅 Recommended schedule: 6-8 hours of study in 90-minute blocks with 15-minute breaks. Tackle hardest subjects when your energy is highest (usually morning).",
        'stress': "😌 Managing stress: take regular breaks, exercise 30 min/day, get 7-8 hours of sleep, practice 4-7-8 breathing, and don't forget to socialize.",
        'exam': "📝 Exam prep: start 2 weeks early, use past papers, practice timed sessions, focus on understanding over memorizing, sleep 8 hours the night before.",
        'note': "📓 Effective notes: use Cornell method (main notes + cues + summary), highlight key concepts, review within 24 hours, then convert to flashcards.",
        'time': "⏰ Time management: use time-blocking, tackle your 3 most important tasks first, batch similar work, and always add 20% buffer time to estimates.",
        'hello': "👋 Hello! I'm StudyBot, your personal academic assistant. Ask me about study techniques, exam tips, time management, or motivation!",
        'hi': "👋 Hey there! Ready to study? Ask me anything about learning strategies, time management, or how to stay motivated!",
        'help': "🤖 I can help with: pomodoro technique, focus strategies, memory improvement, motivation, study schedules, stress management, exam prep, and note-taking. What do you need?",
        'tired': "😴 Feeling tired? Take a 20-minute power nap, drink water, do 10 jumping jacks, or try studying a different subject. Your brain needs variety!",
        'math': "📊 For math: practice daily, work through examples step-by-step, don't just memorize formulas—understand WHY they work. Khan Academy and Wolfram Alpha are great resources!",
        'reading': "📚 Speed reading: preview headings first, minimize subvocalization, use a pointer to guide eyes, and always summarize each section after reading.",
    }
    response = "🤔 Interesting question! Try asking me about: pomodoro, focus, memory tricks, motivation, study schedules, stress management, exam tips, or note-taking strategies!"
    for key, resp in responses.items():
        if key in msg:
            response = resp; break
    return jsonify({'response': response})

@app.route('/api/theme', methods=['POST'])
def update_theme():
    if 'user_id' not in session: return jsonify({'error':'Unauthorized'}),401
    data = request.get_json()
    conn = get_db()
    conn.execute('UPDATE users SET theme=?,color_theme=? WHERE id=?',
                 (data.get('theme','dark'),data.get('color_theme','purple'),session['user_id']))
    conn.commit(); conn.close(); return jsonify({'success':True})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
