from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import json

app = Flask(__name__)
app.secret_key = 'your_very_secret_key_123' 

# Cấu hình SQLAlchemy
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'school_data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Định nghĩa Models ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(120))
    hoten = db.Column(db.String(100), nullable=False)
    lop_chunhiem = db.Column(db.String(10))
    lop = db.Column(db.String(10))
    children_usernames = db.Column(db.String(255))

    sent_messages = db.relationship('Message', foreign_keys='Message.from_user_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.to_user_id', backref='recipient', lazy='dynamic')

    created_events = db.relationship('Event', foreign_keys='Event.created_by_id', backref='creator', lazy=True)

    sent_requests = db.relationship('Request', foreign_keys='Request.from_user_id', backref='request_sender', lazy='dynamic')
    handled_requests = db.relationship('Request', foreign_keys='Request.handler_id', backref='request_handler', lazy='dynamic')

    # Quan hệ cho khen thưởng/kỷ luật (khi User này là người quyết định)
    disciplinary_decisions = db.relationship(
        'DisciplinaryReward',
        foreign_keys='DisciplinaryReward.decision_maker_id', 
        backref='decision_maker_user',
        lazy='dynamic'
    )

    def __repr__(self):
        return f'<User {self.username}>'

    def get_children(self):
        if self.role == 'phuhuynh' and self.children_usernames:
            return User.query.filter(User.username.in_(self.children_usernames.split(','))).all()
        return []

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Message {self.id}>'

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    student_username = db.Column(db.String(80))
    class_name = db.Column(db.String(10))

    def __repr__(self):
        return f'<Event {self.title}>'

class Grade(db.Model):
    __tablename__ = 'grades'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False)

    student = db.relationship('User', foreign_keys=[student_id], backref=db.backref('grades', lazy='dynamic')) 

    __table_args__ = (db.UniqueConstraint('student_id', 'subject', name='_student_subject_uc'),)

    def __repr__(self):
        return f'<Grade {self.student.username if self.student else self.student_id} - {self.subject}: {self.score}>'


class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="Chưa xử lý")
    reply = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    handler_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    handler_timestamp = db.Column(db.DateTime)

    student = db.relationship('User', foreign_keys=[student_id], backref=db.backref('related_requests', lazy='dynamic'))

    def __repr__(self):
        return f'<Request {self.id}>'

class DisciplinaryReward(db.Model):
    __tablename__ = 'disciplinary_rewards'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # User là học sinh
    type = db.Column(db.String(20), nullable=False) # khenthuong, kyluat
    reason = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    decision_maker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # User là người ra quyết định

    student = db.relationship('User', foreign_keys=[student_id], backref=db.backref('disciplinary_records', lazy='dynamic')) # CHỈ ĐỊNH RÕ foreign_keys
    # backref 'decision_maker_user' được tạo từ User.disciplinary_decisions

    def __repr__(self):
        return f'<DisciplinaryReward {self.type} for student_id {self.student_id}>'

# --- Kết thúc định nghĩa Models ---

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

def get_user_details(username_or_id):
    if isinstance(username_or_id, int):
        return User.query.get(username_or_id)
    return User.query.filter_by(username=username_or_id).first()


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        role_form = request.form['role']
        user = User.query.filter_by(username=username).first()

        if user and user.role == role_form:
            session['user_id'] = user.id
            session['user_username'] = user.username
            session['user_hoten'] = user.hoten
            session['role'] = user.role
            flash(f"Đăng nhập thành công với vai trò {user.role}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Tên đăng nhập hoặc vai trò không đúng.", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    current_user = User.query.get(session['user_id'])
    if not current_user:
        session.clear()
        flash("Phiên đăng nhập không hợp lệ, vui lòng đăng nhập lại.", "warning")
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_details=current_user)


@app.route('/messages', methods=['GET', 'POST'])
def messages_route():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    current_user = User.query.get(session['user_id'])

    user_messages = Message.query.filter(
        (Message.to_user_id == current_user.id) | (Message.from_user_id == current_user.id)
    ).order_by(Message.timestamp.asc()).all() # Sắp xếp cũ nhất trước để hiển thị đúng thứ tự

    if request.method == 'POST':
        to_user_username = request.form['to_user']
        content = request.form['content']
        recipient = User.query.filter_by(username=to_user_username).first()

        if not recipient:
            flash(f"Người dùng '{to_user_username}' không tồn tại.", "danger")
        elif recipient.id == current_user.id:
            flash("Bạn không thể gửi tin nhắn cho chính mình.", "warning")
        else:
            new_msg = Message(
                from_user_id=current_user.id,
                to_user_id=recipient.id,
                content=content
            )
            db.session.add(new_msg)
            db.session.commit()
            flash("Tin nhắn đã được gửi!", "success")
            return redirect(url_for('messages_route'))

    users_for_messaging = User.query.filter(User.id != current_user.id).order_by(User.hoten).all()

    return render_template('messages.html',
                           messages=user_messages,
                           current_user_hoten=current_user.hoten,
                           current_user_id=current_user.id,
                           users_for_messaging=users_for_messaging)


@app.route('/events', methods=['GET', 'POST'])
def events_route():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    current_user = User.query.get(session['user_id'])

    display_events = Event.query.order_by(Event.date.desc(), Event.timestamp.desc()).all()

    if request.method == 'POST' and current_user.role in ['giaovien', 'truong']:
        event_type = request.form.get('event_type', 'event')
        try:
            event_date_str = request.form['date']
            if not event_date_str:
                flash("Ngày không được để trống.", "danger")
                return redirect(url_for('events_route'))
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Ngày không hợp lệ. Vui lòng nhập đúng định dạng YYYY-MM-DD.", "danger")
            return redirect(url_for('events_route'))

        title = request.form.get('title')
        description = request.form.get('description')
        if not title or not description:
            flash("Tiêu đề và nội dung không được để trống.", "danger")
            return redirect(url_for('events_route'))

        new_event = Event(
            title=title,
            date=event_date,
            description=description,
            type=event_type,
            created_by_id=current_user.id
        )
        student_username_form = request.form.get('student_username')
        if event_type in ['khenthuong', 'kyluat'] and student_username_form:
            student_for_event = User.query.filter_by(username=student_username_form, role='hocsinh').first()
            if student_for_event:
                new_event.student_username = student_for_event.username
                new_event.class_name = request.form.get('class_name') or student_for_event.lop

                # Thêm vào DisciplinaryReward
                dr_entry = DisciplinaryReward(
                    student_id=student_for_event.id,
                    type=event_type,
                    reason=new_event.description,
                    date=new_event.date,
                    decision_maker_id=current_user.id
                )
                db.session.add(dr_entry)
            else:
                flash(f"Học sinh '{student_username_form}' không tìm thấy.", "warning")
        elif event_type in ['khenthuong', 'kyluat'] and not student_username_form:
             flash("Vui lòng chọn học sinh cho sự kiện khen thưởng/kỷ luật.", "warning")
             # Không thêm event nếu thiếu thông tin quan trọng
        else: # event, thongbao_chung
            pass

        if not (event_type in ['khenthuong', 'kyluat'] and not student_username_form): # Chỉ thêm nếu không phải lỗi thiếu HS
            db.session.add(new_event)
            db.session.commit()
            flash("Sự kiện/Thông báo đã được thêm!", "success")
        return redirect(url_for('events_route'))

    students = User.query.filter_by(role='hocsinh').order_by(User.hoten).all()

    return render_template('events.html',
                           events=display_events,
                           role=current_user.role,
                           students=students,
                           get_user_details=get_user_details)


@app.route('/grades', methods=['GET', 'POST'])
def grades_route():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    current_user = User.query.get(session['user_id'])
    student_grades_display = {}

    if current_user.role == 'hocsinh':
        grades_for_student = Grade.query.filter_by(student_id=current_user.id).all()
        student_grades_display[current_user.username] = {g.subject: g.score for g in grades_for_student}
    elif current_user.role == 'phuhuynh':
        children = current_user.get_children()
        for child in children:
            grades_for_child = Grade.query.filter_by(student_id=child.id).all()
            student_grades_display[child.username] = {g.subject: g.score for g in grades_for_child}
    elif current_user.role in ['giaovien', 'truong']:
        all_students_with_grades = User.query.filter_by(role='hocsinh').outerjoin(Grade).all()
        for s in all_students_with_grades:
            student_grades_display[s.username] = {g.subject: g.score for g in s.grades}


    if request.method == 'POST' and current_user.role == 'giaovien':
        student_username_form = request.form.get('student_username')
        subject_form = request.form.get('subject')
        score_str = request.form.get('score')

        if not student_username_form or not subject_form or not score_str:
            flash("Vui lòng điền đầy đủ thông tin học sinh, môn học và điểm.", "danger")
            return redirect(url_for('grades_route'))
        try:
            score_form = float(score_str)
            if not (0 <= score_form <= 10):
                raise ValueError("Điểm phải từ 0 đến 10.")
        except ValueError as e:
            flash(f"Điểm số không hợp lệ: {e}", "danger")
            return redirect(url_for('grades_route'))

        student_to_grade = User.query.filter_by(username=student_username_form, role='hocsinh').first()
        if not student_to_grade:
            flash(f"Học sinh '{student_username_form}' không tồn tại.", "danger")
        else:
            existing_grade = Grade.query.filter_by(student_id=student_to_grade.id, subject=subject_form).first()
            if existing_grade:
                existing_grade.score = score_form
                flash("Điểm đã được cập nhật!", "success")
            else:
                new_grade = Grade(student_id=student_to_grade.id, subject=subject_form, score=score_form)
                db.session.add(new_grade)
                flash("Điểm đã được thêm mới!", "success")
            db.session.commit()
            return redirect(url_for('grades_route'))

    students_list = User.query.filter_by(role='hocsinh').order_by(User.hoten).all()
    return render_template('grades.html',
                           grades_data=student_grades_display,
                           role=current_user.role,
                           session_user_username=current_user.username,
                           students_list=students_list,
                           get_user_details=get_user_details)


@app.route('/requests', methods=['GET', 'POST'])
def requests_view_route():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    current_user = User.query.get(session['user_id'])
    display_requests = []

    if current_user.role == 'phuhuynh':
        display_requests = Request.query.filter_by(from_user_id=current_user.id).order_by(Request.timestamp.desc()).all()
    elif current_user.role == 'giaovien':
        if current_user.lop_chunhiem:
            student_ids_in_class = [s.id for s in User.query.filter_by(lop=current_user.lop_chunhiem, role='hocsinh').all()]
            display_requests = Request.query.filter(Request.student_id.in_(student_ids_in_class)).order_by(Request.timestamp.desc()).all()
        else:
             display_requests = Request.query.filter(
                (Request.status == 'Chưa xử lý') | (Request.handler_id == current_user.id) # GV xem đơn chưa xử lý hoặc đơn mình đã xử lý
            ).order_by(Request.timestamp.desc()).all()
    elif current_user.role == 'truong':
        display_requests = Request.query.order_by(Request.timestamp.desc()).all()

    if request.method == 'POST':
        if current_user.role == 'phuhuynh':
            student_username_form = request.form.get('student_username')
            content_form = request.form.get('content')

            if not student_username_form or not content_form:
                flash("Vui lòng chọn học sinh và nhập nội dung đơn.", "danger")
                return redirect(url_for('requests_view_route'))

            student_for_request = User.query.filter_by(username=student_username_form, role='hocsinh').first()
            is_child = False
            if student_for_request and current_user.children_usernames:
                if student_username_form in current_user.children_usernames.split(','):
                    is_child = True

            if not student_for_request or not is_child:
                flash("Học sinh không hợp lệ hoặc không phải con em của bạn.", "danger")
            else:
                new_req_db = Request(
                    from_user_id=current_user.id,
                    student_id=student_for_request.id,
                    content=content_form
                )
                db.session.add(new_req_db)
                db.session.commit()
                flash("Đơn đã được gửi!", "success")

        elif current_user.role in ['giaovien', 'truong']:
            req_id_form = request.form.get('req_id')
            reply_content_form = request.form.get('reply')
            new_status_form = request.form.get('status')

            if not req_id_form or not new_status_form:
                flash("Thiếu thông tin đơn hoặc trạng thái mới.", "danger")
                return redirect(url_for('requests_view_route'))
            try:
                req_id_form = int(req_id_form)
            except ValueError:
                flash("ID đơn không hợp lệ.", "danger")
                return redirect(url_for('requests_view_route'))


            req_to_update = Request.query.get(req_id_form)
            if req_to_update:
                if reply_content_form: # Cho phép cập nhật reply trống
                    req_to_update.reply = reply_content_form
                req_to_update.status = new_status_form
                req_to_update.handler_id = current_user.id
                req_to_update.handler_timestamp = datetime.utcnow()
                db.session.commit()
                flash("Đơn đã được xử lý!", "success")
            else:
                flash("Không tìm thấy đơn yêu cầu.", "warning")
        return redirect(url_for('requests_view_route'))

    children_list = []
    if current_user.role == 'phuhuynh':
       children_list = current_user.get_children()

    return render_template('requests.html',
                           requests_data=display_requests,
                           role=current_user.role,
                           get_user_details=get_user_details,
                           children_list=children_list)


@app.route('/statistics')
def statistics():
    if 'user_id' not in session or session['role'] not in ['giaovien', 'truong']:
        flash("Bạn không có quyền truy cập trang này.", "warning")
        return redirect(url_for('dashboard'))

    num_students = User.query.filter_by(role='hocsinh').count()
    num_teachers = User.query.filter_by(role='giaovien').count()
    num_requests_pending = Request.query.filter(Request.status.in_(['Chưa xử lý', 'Đang xử lý'])).count()
    num_events = Event.query.count()
    rewards_count = DisciplinaryReward.query.filter_by(type='khenthuong').count()
    discipline_count = DisciplinaryReward.query.filter_by(type='kyluat').count()

    avg_math_score_query = db.session.query(func.avg(Grade.score)).filter(Grade.subject == 'Toán').scalar()
    avg_math_score = round(avg_math_score_query, 2) if avg_math_score_query else "N/A"

    stats = {
        "num_students": num_students,
        "num_teachers": num_teachers,
        "num_requests_pending": num_requests_pending,
        "num_events_announcements": num_events,
        "rewards_count": rewards_count,
        "discipline_count": discipline_count,
        "avg_math_score": avg_math_score
    }
    return render_template('statistics.html', stats=stats, role=session['role'])


@app.route('/logout')
def logout():
    session.clear()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for('login'))


def init_db_and_migrate():
    print("Khởi tạo cơ sở dữ liệu và di chuyển dữ liệu từ JSON...")
    # db.drop_all() # 
    db.create_all()

    json_data_file = os.path.join(BASE_DIR, 'data.json')
    if not os.path.exists(json_data_file):
        print(f"Không tìm thấy file {json_data_file}. Bỏ qua migration.")
        return

    try:
        with open(json_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Lỗi khi đọc data.json: {e}")
        return

    users_map = {}
    print("Migrating Users...")
    for u_data in data.get('users', []):
        if not User.query.filter_by(username=u_data['username']).first():
            user = User(
                username=u_data['username'],
                role=u_data['role'],
                password_hash=u_data.get('password_hash', 'default_pwd_placeholder'),
                hoten=u_data['hoten'],
                lop_chunhiem=u_data.get('lop_chunhiem'),
                lop=u_data.get('lop'),
                children_usernames=",".join(u_data.get('con_em', [])) if u_data.get('con_em') else None
            )
            db.session.add(user)
            try:
                db.session.commit()
                users_map[user.username] = user.id
                print(f"  Added user: {user.username}")
            except Exception as e_commit:
                db.session.rollback()
                print(f"  Error adding user {u_data['username']} on commit: {e_commit}")
        else:
            existing_user = User.query.filter_by(username=u_data['username']).first()
            users_map[existing_user.username] = existing_user.id # Vẫn map user đã tồn tại
            print(f"  User {u_data['username']} already exists.")


    print("\nMigrating Messages...")
    for m_data in data.get('messages', []):
        from_user_id = users_map.get(m_data['from_user'])
        to_user_id = users_map.get(m_data['to_user'])
        if from_user_id and to_user_id:
            msg_timestamp = datetime.strptime(m_data['timestamp'], "%Y-%m-%d %H:%M:%S")
            if not Message.query.filter_by(from_user_id=from_user_id, to_user_id=to_user_id, timestamp=msg_timestamp).first():
                msg = Message(
                    from_user_id=from_user_id, to_user_id=to_user_id, content=m_data['content'],
                    timestamp=msg_timestamp, read=m_data.get('read', False)
                )
                db.session.add(msg)
                print(f"  Added message from {m_data['from_user']} to {m_data['to_user']}")
        else:
            print(f"  Skipping message: missing user for from_user='{m_data['from_user']}' or to_user='{m_data['to_user']}'")
    db.session.commit()


    print("\nMigrating Events...")
    for e_data in data.get('events', []):
        created_by_id = users_map.get(e_data['created_by'])
        if created_by_id:
            event_date = datetime.strptime(e_data['date'], "%Y-%m-%d").date()
            event_timestamp = datetime.strptime(e_data['timestamp'], "%Y-%m-%d %H:%M:%S")
            if not Event.query.filter_by(title=e_data['title'], date=event_date, created_by_id=created_by_id).first():
                event = Event(
                    title=e_data['title'], date=event_date, description=e_data['description'], type=e_data['type'],
                    created_by_id=created_by_id, timestamp=event_timestamp,
                    student_username=e_data.get('student_username'), class_name=e_data.get('class_name')
                )
                db.session.add(event)
                print(f"  Added event: {event.title}")
        else:
            print(f"  Skipping event: missing creator_id for {e_data['created_by']}")
    db.session.commit()

    print("\nMigrating Grades...")
    for student_username, subjects in data.get('grades', {}).items():
        student_id = users_map.get(student_username)
        if student_id:
            for subject, score in subjects.items():
                existing_grade = Grade.query.filter_by(student_id=student_id, subject=subject).first()
                if not existing_grade:
                    grade = Grade(student_id=student_id, subject=subject, score=score)
                    db.session.add(grade)
                    print(f"  Added grade for {student_username}: {subject} - {score}")
                else: # Cập nhật điểm nếu đã có
                    existing_grade.score = score
                    print(f"  Updated grade for {student_username}: {subject} to {score}")
        else:
            print(f"  Skipping grades: missing student_id for {student_username}")
    db.session.commit()

    print("\nMigrating Requests...")
    for r_data in data.get('requests', []):
        from_user_id = users_map.get(r_data['from_user'])
        student_id_req = users_map.get(r_data['student_username'])
        handler_id_req = users_map.get(r_data['handler']) if r_data.get('handler') else None
        if from_user_id and student_id_req:
            req_timestamp = datetime.strptime(r_data['timestamp'], "%Y-%m-%d %H:%M:%S")
            handler_ts_req = datetime.strptime(r_data['handler_timestamp'], "%Y-%m-%d %H:%M:%S") if r_data.get('handler_timestamp') else None
            # Giả sử ID trong JSON không dùng để check, check dựa trên from, student, content, timestamp
            if not Request.query.filter_by(from_user_id=from_user_id, student_id=student_id_req, content=r_data['content'], timestamp=req_timestamp).first():
                req = Request(
                    from_user_id=from_user_id, student_id=student_id_req, content=r_data['content'],
                    status=r_data.get('status', "Chưa xử lý"), reply=r_data.get('reply'),
                    timestamp=req_timestamp, handler_id=handler_id_req, handler_timestamp=handler_ts_req
                )
                db.session.add(req)
                print(f"  Added request from {r_data['from_user']} for {r_data['student_username']}")
        else:
            print(f"  Skipping request: missing user for from_user='{r_data['from_user']}' or student='{r_data['student_username']}'")
    db.session.commit()

    print("\nMigrating Disciplinary Rewards...")
    for dr_data in data.get('disciplinary_rewards', []):
        student_id_dr = users_map.get(dr_data['student_username'])
        decision_maker_id_dr = users_map.get(dr_data['decision_maker'])
        if student_id_dr and decision_maker_id_dr:
            dr_date = datetime.strptime(dr_data['date'], "%Y-%m-%d").date()
            if not DisciplinaryReward.query.filter_by(student_id=student_id_dr, type=dr_data['type'], date=dr_date, decision_maker_id=decision_maker_id_dr).first():
                dr = DisciplinaryReward(
                    student_id=student_id_dr, type=dr_data['type'], reason=dr_data['reason'],
                    date=dr_date, decision_maker_id=decision_maker_id_dr
                )
                db.session.add(dr)
                print(f"  Added {dr_data['type']} for {dr_data['student_username']}")
        else:
            print(f"  Skipping disciplinary_reward: missing user for student='{dr_data['student_username']}' or decision_maker='{dr_data['decision_maker']}'")
    db.session.commit()

    print("\nDi chuyển dữ liệu hoàn tất!")


if __name__ == '__main__':
    db_file = os.path.join(BASE_DIR, 'school_data.db')
    if not os.path.exists(db_file):
        with app.app_context():
            init_db_and_migrate()
    else:
        print("Database file đã tồn tại. Bỏ qua bước khởi tạo và di chuyển dữ liệu.")
    app.run(debug=True)