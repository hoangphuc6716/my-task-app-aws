from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Task  # Import thêm Task
import os
import socket
from sqlalchemy import text # <-- THÊM DÒNG NÀY

app = Flask(__name__)

# --- CẤU HÌNH MỚI ---
# Đọc cấu hình từ biến môi trường (AWS sẽ cung cấp các biến này)
app.config.update(
    # Lấy SECRET_KEY từ biến môi trường
    SECRET_KEY=os.environ.get('SECRET_KEY', 'default-key-for-local-dev'),
    
    # Lấy DATABASE_URI từ biến môi trường
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URI', 'sqlite:///local_app.db'),
    
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)
# ---------------------

# Khởi tạo DB và LoginManager
db.init_app(app)

with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#@app.before_first_request
#def create_tables():
    # Hàm này sẽ tự động tạo các bảng khi chạy lần đầu
    # Rất hữu ích cho việc khởi tạo database trên AWS
   # db.create_all()

def get_system_info():
    try:
        # Lấy hostname để xem container nào đang xử lý request
        return {
            'hostname': socket.gethostname()
        }
    except Exception:
        return {'hostname': 'unknown'}

# --- CÁC ROUTE GIAO DIỆN (ĐÃ SỬA) ---
@app.route('/')
@login_required
def index():
    # Sửa: Lấy task từ DB của user này, thay vì từ file JSON
    tasks_from_db = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_at.desc()).all()
    tasks_list = [task.to_dict() for task in tasks_from_db]
    
    # Truyền system_info vào template
    return render_template('index.html', tasks=tasks_list, system_info=get_system_info())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Sai tên đăng nhập hoặc mật khẩu')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Tên đăng nhập hoặc email đã tồn tại')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Đăng ký thành công! Vui lòng đăng nhập.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- CÁC ROUTE API (ĐÃ VIẾT LẠI HOÀN TOÀN) ---

@app.route('/api/tasks', methods=['GET'])
@login_required
def get_tasks():
    # Sửa: Lấy task của user đang đăng nhập từ DB
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return jsonify([task.to_dict() for task in tasks])

@app.route('/api/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400
        
    # Sửa: Tạo object Task mới và lưu vào DB
    new_task = Task(
        title=data['title'],
        description=data.get('description', ''),
        priority=data.get('priority', 'medium'),
        user_id=current_user.id  # <-- Gán task cho user
    )
    db.session.add(new_task)
    db.session.commit()
    
    return jsonify(new_task.to_dict()), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = db.session.get(Task, task_id) # <-- Sửa: Dùng db.session.get
    
    # Kiểm tra task có tồn tại và thuộc về user này không
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    if task.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    
    # Sửa: Cập nhật các trường và lưu vào DB
    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        task.status = data['status']
    if 'priority' in data:
        task.priority = data['priority']
        
    db.session.commit()
    return jsonify(task.to_dict()), 200

# --- HEALTH CHECK CHO LOAD BALANCER ---
# ĐÃ SỬA:
@app.route('/health')
def health_check():
    try:
        # Gửi một câu lệnh đơn giản để kiểm tra kết nối DB
        db.session.execute(text('SELECT 1')) 
        return "OK", 200 # Trả về 200 NẾU kết nối DB thành công
    except Exception as e:
        # Ghi log lỗi để debug
        print(f"Health check failed: {e}", flush=True) 
        # Trả về 500 NẾU kết nối DB thất bại
        return f"Health check failed: {e}", 500
    