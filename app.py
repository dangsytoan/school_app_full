from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_very_secret_key_123' # Thay đổi key này!

DATA_FILE = 'data.json'

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

def load_data():
    if not os.path.exists(DATA_FILE):
        # Tạo file data.json mẫu nếu chưa có
        sample_data = {
            "users": [
                {"username": "bgh_hieu_truong", "role": "truong", "password_hash": "admin_pwd", "hoten": "Thầy Hiệu Trưởng", "lop_chunhiem": null},
                {"username": "gv_toan_thay_hung", "role": "giaovien", "password_hash": "gv_pwd", "hoten": "Thầy Mạnh Hùng", "lop_chunhiem": "10A1"},
                {"username": "gv_van_co_mai", "role": "giaovien", "password_hash": "gv_pwd", "hoten": "Cô Thanh Mai", "lop_chunhiem": "11B2"},
                {"username": "gv_anh_co_lan", "role": "giaovien", "password_hash": "gv_pwd", "hoten": "Cô Ngọc Lan", "lop_chunhiem": "12C3"},
                {"username": "hs_an_nguyen", "role": "hocsinh", "password_hash": "hs_pwd", "hoten": "Nguyễn Văn An", "lop": "10A1"},
                {"username": "hs_binh_le", "role": "hocsinh", "password_hash": "hs_pwd", "hoten": "Lê Thị Bình", "lop": "10A1"},
                {"username": "hs_chi_tran", "role": "hocsinh", "password_hash": "hs_pwd", "hoten": "Trần Minh Chi", "lop": "11B2"},
                {"username": "hs_dung_pham", "role": "hocsinh", "password_hash": "hs_pwd", "hoten": "Phạm Tuấn Dũng", "lop": "11B2"},
                {"username": "hs_giang_hoang", "role": "hocsinh", "password_hash": "hs_pwd", "hoten": "Hoàng Thu Giang", "lop": "12C3"},
                {"username": "hs_khanh_vu", "role": "hocsinh", "password_hash": "hs_pwd", "hoten": "Vũ Đăng Khánh", "lop": "12C3"},
                {"username": "ph_an_nguyen_bo", "role": "phuhuynh", "password_hash": "ph_pwd", "hoten": "Ông Nguyễn Văn Ba", "con_em": ["hs_an_nguyen"]},
                {"username": "ph_binh_le_me", "role": "phuhuynh", "password_hash": "ph_pwd", "hoten": "Bà Lê Thị Tư", "con_em": ["hs_binh_le"]},
                {"username": "ph_chi_tran_bo", "role": "phuhuynh", "password_hash": "ph_pwd", "hoten": "Ông Trần Văn Năm", "con_em": ["hs_chi_tran"]},
                {"username": "ph_dung_pham_me", "role": "phuhuynh", "password_hash": "ph_pwd", "hoten": "Bà Phạm Thị Sáu", "con_em": ["hs_dung_pham"]},
                {"username": "ph_giang_hoang_bo", "role": "phuhuynh", "password_hash": "ph_pwd", "hoten": "Ông Hoàng Văn Bảy", "con_em": ["hs_giang_hoang"]},
                {"username": "ph_khanh_vu_me", "role": "phuhuynh", "password_hash": "ph_pwd", "hoten": "Bà Vũ Thị Tám", "con_em": ["hs_khanh_vu", "hs_an_nguyen"]}
            ],
            "messages": [
                {"id": 1, "from_user": "gv_toan_thay_hung", "to_user": "ph_an_nguyen_bo", "content": "Xin chào anh Ba, mời anh tham dự buổi họp phụ huynh lớp 10A1 vào thứ 7 tuần này.", "timestamp": "2025-05-10 08:30:00", "read": false},
                {"id": 2, "from_user": "ph_an_nguyen_bo", "to_user": "gv_toan_thay_hung", "content": "Cảm ơn thầy Hùng, tôi sẽ cố gắng tham dự.", "timestamp": "2025-05-10 09:15:00", "read": false},
                {"id": 3, "from_user": "bgh_hieu_truong", "to_user": "gv_van_co_mai", "content": "Cô Mai vui lòng nộp báo cáo chuyên môn trước ngày 15/05.", "timestamp": "2025-05-11 10:00:00", "read": false},
                {"id": 4, "from_user": "gv_van_co_mai", "to_user": "bgh_hieu_truong", "content": "Dạ vâng thưa thầy, tôi sẽ hoàn thành sớm ạ.", "timestamp": "2025-05-11 10:05:00", "read": false},
                {"id": 5, "from_user": "hs_chi_tran", "to_user": "gv_van_co_mai", "content": "Thưa cô, em có câu hỏi về bài tập về nhà ạ.", "timestamp": "2025-05-12 14:20:00", "read": false},
                {"id": 6, "from_user": "gv_anh_co_lan", "to_user": "ph_khanh_vu_me", "content": "Chào chị Tám, kết quả học tập môn Tiếng Anh của cháu Khánh rất tốt.", "timestamp": "2025-05-12 16:00:00", "read": false}
            ],
            "events": [
                {"id": 1, "title": "Thông báo Nghỉ lễ Giỗ Tổ Hùng Vương", "date": "2025-04-18", "description": "Toàn thể học sinh, giáo viên được nghỉ lễ Giỗ Tổ Hùng Vương ngày 10/3 Âm lịch (tức 18/04/2025 Dương lịch).", "type": "thongbao_chung", "created_by": "bgh_hieu_truong", "timestamp": "2025-04-15 08:00:00"},
                {"id": 2, "title": "Lịch thi học kỳ II Khối 10, 11", "date": "2025-05-19", "description": "Lịch thi chi tiết học kỳ II cho học sinh khối 10 và 11 sẽ diễn ra từ ngày 19/05 đến 24/05. Chi tiết xem tại bảng tin nhà trường.", "type": "event", "created_by": "bgh_hieu_truong", "timestamp": "2025-05-05 09:00:00"},
                {"id": 3, "title": "Khen thưởng học sinh Nguyễn Văn An - Lớp 10A1", "date": "2025-05-10", "description": "Học sinh Nguyễn Văn An lớp 10A1 được tuyên dương vì đã đạt giải Nhất cuộc thi Học sinh Giỏi môn Toán cấp Thành phố.", "type": "khenthuong", "student_username": "hs_an_nguyen", "class_name": "10A1", "created_by": "gv_toan_thay_hung", "timestamp": "2025-05-10 10:00:00"},
                {"id": 4, "title": "Hoạt động ngoại khóa: Tham quan Bảo tàng Lịch sử", "date": "2025-05-28", "description": "Tổ chức cho học sinh khối 11 tham quan Bảo tàng Lịch sử Quốc gia. Thời gian: 8h00 ngày 28/05. Phụ huynh đăng ký cho con em tại văn phòng Đoàn trường.", "type": "event", "created_by": "bgh_hieu_truong", "timestamp": "2025-05-12 11:00:00"},
                {"id": 5, "title": "Kỷ luật học sinh Phạm Tuấn Dũng - Lớp 11B2", "date": "2025-05-08", "description": "Học sinh Phạm Tuấn Dũng lớp 11B2 bị kỷ luật cảnh cáo toàn trường do vi phạm nghiêm trọng nội quy về giờ giấc.", "type": "kyluat", "student_username": "hs_dung_pham", "class_name": "11B2", "created_by": "gv_van_co_mai", "timestamp": "2025-05-08 14:00:00"},
                {"id": 6, "title": "Thông báo họp giáo viên toàn trường", "date": "2025-05-16", "description": "Kính mời toàn thể giáo viên tham dự buổi họp tổng kết tháng và triển khai công tác tháng mới. Thời gian: 15h00, Thứ Sáu ngày 16/05 tại Hội trường A.", "type": "thongbao_chung", "created_by": "bgh_hieu_truong", "timestamp": "2025-05-13 16:30:00"}
            ],
            "grades": {
                "hs_an_nguyen": {
                    "Toán": 9.5, "Vật Lý": 8.0, "Hóa Học": 8.5, "Ngữ Văn": 7.5, "Tiếng Anh": 9.0
                },
                "hs_binh_le": {
                    "Toán": 7.0, "Vật Lý": 6.5, "Hóa Học": 7.0, "Ngữ Văn": 8.0, "Tiếng Anh": 7.5
                },
                "hs_chi_tran": {
                    "Toán": 8.5, "Ngữ Văn": 9.0, "Tiếng Anh": 8.8, "Lịch Sử": 7.0, "Địa Lý": 7.5
                },
                "hs_dung_pham": {
                    "Toán": 6.0, "Ngữ Văn": 6.5, "Tiếng Anh": 7.0, "Lịch Sử": 5.5, "Địa Lý": 6.0
                },
                "hs_giang_hoang": {
                    "Tiếng Anh": 9.2, "Ngữ Văn": 8.0, "Toán": 7.5, "Sinh Học": 8.5, "GDCD": 9.0
                },
                "hs_khanh_vu": {
                    "Tiếng Anh": 8.5, "Ngữ Văn": 7.0, "Toán": 8.0, "Sinh Học": 7.0, "GDCD": 8.0
                }
            },
            "requests": [
                {"id": 1, "from_user": "ph_an_nguyen_bo", "student_username": "hs_an_nguyen", "content": "Xin phép cho cháu An nghỉ học buổi chiều ngày 12/05/2025 để đi khám bệnh.", "status": "Đã duyệt", "reply": "Nhà trường đồng ý. Chúc cháu sớm khỏe.", "timestamp": "2025-05-11 08:00:00", "handler": "gv_toan_thay_hung", "handler_timestamp": "2025-05-11 09:30:00"},
                {"id": 2, "from_user": "ph_chi_tran_bo", "student_username": "hs_chi_tran", "content": "Kính mong nhà trường xem xét về việc tăng cường thêm các buổi ôn tập môn Toán cho học sinh khối 11.", "status": "Đang xử lý", "reply": "Cảm ơn ý kiến của phụ huynh. Nhà trường sẽ xem xét và có phản hồi sớm.", "timestamp": "2025-05-12 10:15:00", "handler": "bgh_hieu_truong", "handler_timestamp": "2025-05-12 11:00:00"},
                {"id": 3, "from_user": "ph_dung_pham_me", "student_username": "hs_dung_pham", "content": "Xin giải trình về việc cháu Dũng đi học muộn ngày 07/05/2025 do xe hỏng.", "status": "Chưa xử lý", "reply": "", "timestamp": "2025-05-09 07:30:00", "handler": null},
                {"id": 4, "from_user": "ph_khanh_vu_me", "student_username": "hs_khanh_vu", "content": "Xin phép cho cháu Khánh được rút học bạ để chuyển trường.", "status": "Đã từ chối", "reply": "Vui lòng liên hệ trực tiếp văn phòng nhà trường để được hướng dẫn thủ tục chi tiết. Việc rút học bạ cần có lý do chính đáng và tuân thủ quy định.", "timestamp": "2025-04-20 14:00:00", "handler": "bgh_hieu_truong", "handler_timestamp": "2025-04-22 10:00:00"}
            ],
            "disciplinary_rewards": [
                {"id": 1, "student_username": "hs_an_nguyen", "type": "khenthuong", "reason": "Đạt giải Nhất cuộc thi Học sinh Giỏi môn Toán cấp Thành phố.", "date": "2025-05-09", "decision_maker": "bgh_hieu_truong"},
                {"id": 2, "student_username": "hs_giang_hoang", "type": "khenthuong", "reason": "Có nhiều đóng góp tích cực cho phong trào Đoàn trường.", "date": "2025-04-25", "decision_maker": "gv_anh_co_lan"},
                {"id": 3, "student_username": "hs_dung_pham", "type": "kyluat", "reason": "Vi phạm nghiêm trọng nội quy về giờ giấc (đi học muộn nhiều lần).", "date": "2025-05-07", "decision_maker": "gv_van_co_mai"},
                {"id": 4, "student_username": "hs_binh_le", "type": "khenthuong", "reason": "Tiến bộ vượt bậc trong học tập môn Ngữ Văn.", "date": "2025-05-12", "decision_maker": "gv_van_co_mai"}
            ]
        }
        save_data(sample_data)
        return sample_data
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# Hàm save_data không đổi
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_user_details(username):
    data = load_data()
    for user in data['users']:
        if user['username'] == username:
            return user
    return None

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        # Trong thực tế cần kiểm tra password hash
        # For demo, chúng ta sẽ bỏ qua kiểm tra password và chỉ cần user tồn tại
        data = load_data()
        user_exists = False
        user_role = None
        for u in data['users']:
            if u['username'] == username:
                user_exists = True
                user_role = u['role']
                session['user_hoten'] = u.get('hoten', username) # Lấy họ tên
                break

        if user_exists and request.form['role'] == user_role:
            session['user'] = username
            session['role'] = user_role
            flash(f"Đăng nhập thành công với vai trò {user_role}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Tên đăng nhập hoặc vai trò không đúng.", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    user_details = get_user_details(session['user'])
    return render_template('dashboard.html', user=session.get('user_hoten', session['user']), role=session['role'], user_details=user_details)

@app.route('/messages', methods=['GET', 'POST'])
def messages_route(): 
    if 'user' not in session:
        return redirect(url_for('login'))

    data = load_data()

    user_messages = [msg for msg in data.get('messages', []) if msg.get('to_user') == session['user'] or msg.get('from_user') == session['user']]
    user_messages = sorted(user_messages, key=lambda x: x.get('timestamp', ''), reverse=True) # Sắp xếp tin nhắn mới nhất lên đầu


    if request.method == 'POST':
        to_user = request.form['to_user']
        content = request.form['content']

        recipient_exists = any(u['username'] == to_user for u in data['users'])
        if not recipient_exists:
            flash(f"Người dùng '{to_user}' không tồn tại.", "danger")
        else:
            new_msg = {
                "id": len(data['messages']) + 1,
                "from_user": session['user'],
                "to_user": to_user,
                "content": content,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "read": False
            }
            data['messages'].append(new_msg)
            save_data(data)
            flash("Tin nhắn đã được gửi!", "success")
            return redirect(url_for('messages_route')) # Chuyển hướng sau khi POST để tránh gửi lại form

    # Lấy danh sách người dùng để gợi ý người nhận (trừ chính mình)
    # Đảm bảo data['users'] luôn tồn tại
    users_for_messaging = [u for u in data.get('users', []) if u['username'] != session['user']]

    return render_template('messages.html',
                           messages=user_messages,
                           current_user_hoten=session.get('user_hoten', session['user']),
                           current_user_username=session['user'],
                           users_for_messaging=users_for_messaging,
                           get_user_details=get_user_details) # Truyền hàm get_user_details vào template


@app.route('/events', methods=['GET', 'POST'])
def events_route(): # Đổi tên hàm
    if 'user' not in session:
        return redirect(url_for('login'))
    data = load_data() # Đảm bảo data được load
    # Lọc sự kiện: BGH và GV thấy hết, PH và HS chỉ thấy sự kiện chung (hoặc liên quan đến lớp nếu có)
    # Hiện tại demo sẽ cho tất cả user thấy tất cả sự kiện/thông báo
    display_events = sorted(data.get('events', []), key=lambda x: x.get('date'), reverse=True)

    if request.method == 'POST' and session['role'] in ['giaovien', 'truong']:
        event_type = request.form.get('event_type', 'event') # Mặc định là event
        new_event = {
            "id": len(data['events']) + 1,
            "title": request.form['title'],
            "date": request.form['date'],
            "description": request.form['description'],
            "type": event_type, # Phân loại: event, khenthuong, kyluat, thongbao_chung
            "created_by": session['user'],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        if event_type in ['khenthuong', 'kyluat']:
            new_event["student_username"] = request.form.get('student_username') # Cần form nhập tên HS
            new_event["class_name"] = request.form.get('class_name') # Cần form nhập lớp

        data['events'].append(new_event)

        # Nếu là khen thưởng/kỷ luật, cũng thêm vào mục disciplinary_rewards để dễ thống kê
        if event_type in ['khenthuong', 'kyluat'] and new_event.get("student_username"):
            dr_entry = {
                "id": len(data.get('disciplinary_rewards', [])) + 1,
                "student_username": new_event["student_username"],
                "type": event_type,
                "reason": new_event["description"], # Lấy mô tả làm lý do
                "date": new_event["date"],
                "decision_maker": session['user']
            }
            data.setdefault('disciplinary_rewards', []).append(dr_entry)

        save_data(data)
        flash("Sự kiện/Thông báo đã được thêm!", "success")
        return redirect(url_for('events_route'))

    # Lấy danh sách học sinh để chọn cho khen thưởng/kỷ luật
    students = [u for u in data.get('users',[]) if u['role'] == 'hocsinh'] 

    return render_template('events.html',
                           events=display_events,
                           role=session['role'],
                           students=students,
                           get_user_details=get_user_details)

@app.route('/grades', methods=['GET', 'POST'])
def grades_route(): # Đổi tên hàm
    if 'user' not in session:
        return redirect(url_for('login'))
    data = load_data()
    user_details = get_user_details(session['user'])
    student_grades = {}

    if session['role'] == 'hocsinh':
        student_grades = {session['user']: data['grades'].get(session['user'], {})}
    elif session['role'] == 'phuhuynh':
        if user_details and 'con_em' in user_details:
            for child_username in user_details['con_em']:
                student_grades[child_username] = data['grades'].get(child_username, {})
    elif session['role'] in ['giaovien', 'truong']: # GV, BGH xem được tất cả
        student_grades = data['grades']


    if request.method == 'POST' and session['role'] == 'giaovien':
        student_username = request.form['student_username']
        subject = request.form['subject']
        try:
            score = float(request.form['score'])
            if not (0 <= score <= 10):
                raise ValueError("Điểm không hợp lệ")
        except ValueError:
            flash("Điểm số không hợp lệ. Vui lòng nhập số từ 0 đến 10.", "danger")
            return redirect(url_for('grades_route'))

        # Kiểm tra học sinh có tồn tại không
        if not any(u['username'] == student_username and u['role'] == 'hocsinh' for u in data['users']):
            flash(f"Học sinh '{student_username}' không tồn tại.", "danger")
        else:
            if student_username not in data['grades']:
                data['grades'][student_username] = {}
            data['grades'][student_username][subject] = score
            save_data(data)
            flash("Điểm đã được cập nhật!", "success")
            return redirect(url_for('grades_route'))

    # Lấy danh sách học sinh để giáo viên nhập điểm
    students_list = [u for u in data['users'] if u['role'] == 'hocsinh']
    return render_template('grades.html', grades_data=student_grades, role=session['role'], students_list=students_list, get_user_details=get_user_details)


@app.route('/requests', methods=['GET', 'POST'])
def requests_view_route(): # Đổi tên hàm
    if 'user' not in session:
        return redirect(url_for('login'))
    data = load_data()
    user_details = get_user_details(session['user'])
    display_requests = []

    if session['role'] == 'phuhuynh':
        display_requests = [req for req in data['requests'] if req.get('from_user') == session['user']]
    elif session['role'] == 'giaovien':
        # GV chủ nhiệm xem đơn của HS lớp mình, hoặc BGH xem tất cả (cần logic phức tạp hơn nếu theo ERD)
        display_requests = data['requests'] # Đơn giản hóa: GV xem hết
    elif session['role'] == 'truong':
        display_requests = data['requests'] # BGH xem hết

    if request.method == 'POST':
        if session['role'] == 'phuhuynh':
            student_username = request.form.get('student_username') # PH cần chọn con nào
            # Kiểm tra student_username có phải là con của phụ huynh này không
            if not (user_details and student_username in user_details.get('con_em',[])):
                flash("Bạn chỉ có thể gửi đơn cho con em của mình.", "danger")
                return redirect(url_for('requests_view_route'))

            new_req = {
                "id": len(data['requests']) + 1,
                "from_user": session['user'],
                "student_username": student_username,
                "content": request.form['content'],
                "status": "Chưa xử lý", # "Chưa xử lý", "Đang xử lý", "Đã duyệt", "Đã từ chối"
                "reply": "",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "handler": None
            }
            data['requests'].append(new_req)
            flash("Đơn đã được gửi!", "success")
        elif session['role'] in ['giaovien', 'truong']:
            req_id = int(request.form['req_id'])
            reply_content = request.form.get('reply')
            new_status = request.form.get('status')

            for req in data['requests']:
                if req['id'] == req_id:
                    if reply_content:
                        req['reply'] = reply_content
                    if new_status:
                        req['status'] = new_status
                    req['handler'] = session['user']
                    req['handler_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    flash("Đơn đã được xử lý!", "success")
                    break
        save_data(data)
        return redirect(url_for('requests_view_route'))

    # Lấy danh sách học sinh (con cái) cho phụ huynh chọn khi gửi đơn
    children_list = []
    if session['role'] == 'phuhuynh' and user_details and 'con_em' in user_details:
        children_list = [get_user_details(child_uname) for child_uname in user_details['con_em'] if get_user_details(child_uname)]


    return render_template('requests.html', requests_data=display_requests, role=session['role'], current_user=session['user'], children_list=children_list, get_user_details=get_user_details)

@app.route('/statistics')
def statistics():
    if 'user' not in session or session['role'] not in ['giaovien', 'truong']:
        flash("Bạn không có quyền truy cập trang này.", "warning")
        return redirect(url_for('dashboard'))

    data = load_data()
    num_students = len([u for u in data['users'] if u['role'] == 'hocsinh'])
    num_teachers = len([u for u in data['users'] if u['role'] == 'giaovien'])
    num_requests_pending = len([r for r in data.get('requests', []) if r.get('status') == 'Chưa xử lý'])
    num_events = len(data.get('events', []))

    # Thống kê khen thưởng/kỷ luật (đơn giản)
    rewards_count = len([dr for dr in data.get('disciplinary_rewards', []) if dr.get('type') == 'khenthuong'])
    discipline_count = len([dr for dr in data.get('disciplinary_rewards', []) if dr.get('type') == 'kyluat'])


    # Thống kê điểm trung bình môn (ví dụ môn Toán)
    # Cần logic phức tạp hơn nếu muốn tính theo lớp, theo kỳ
    math_scores = []
    for student, subjects in data.get('grades', {}).items():
        if 'Toán' in subjects:
            math_scores.append(subjects['Toán'])
    avg_math_score = sum(math_scores) / len(math_scores) if math_scores else "N/A"

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

if __name__ == '__main__':
    app.run(debug=True)