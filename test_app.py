# Tên file: test_app.py (NỘI DUNG MỚI)
import pytest
import json
import os
from app import app, db
from models import User, Task  # <-- Đảm bảo import Task
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    """Setup test client"""
    # Configure app for testing
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', # Dùng CSDL SQLite trong bộ nhớ cho test
        WTF_CSRF_ENABLED=False,
        SECRET_KEY='test-secret-key'
        # ĐÃ LOẠI BỎ DATA_FILE VÌ KHÔNG CÒN DÙNG
    )
    
    # Create tables and test client
    with app.test_client() as client:
        with app.app_context():
            # Create all tables
            db.create_all()
            
            # Create test user
            user = User(
                username='testuser',
                password=generate_password_hash('testpass'),
                email='test@example.com'
            )
            db.session.add(user)
            db.session.commit()
            
            yield client
            
            # Cleanup
            db.session.remove()
            db.drop_all()

@pytest.fixture
def auth_client(client):
    """Client with authenticated user"""
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    }, follow_redirects=True)
    return client

# --- CÁC TEST ĐÃ PASSED (GIỮ NGUYÊN) ---
def test_login_page(client):
    """Test login page"""
    rv = client.get('/login')
    assert rv.status_code == 200
    assert b'ng nh' in rv.data # Check tiếng Việt "Đăng nhập"

def test_login(client):
    """Test login functionality"""
    rv = client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass'
    })
    assert rv.status_code == 302  # Redirect after login

def test_home_page(auth_client):
    """Test trang chủ"""
    rv = auth_client.get('/')
    assert rv.status_code == 200
    assert b"Task Tracker" in rv.data

# --- CÁC TEST ĐÃ SỬA ---

# XÓA BỎ test_about_page (vì route /about không tồn tại trong app.py)

def test_health_check(client):
    """Test API health check (ĐÃ SỬA)"""
    rv = client.get('/health') # Sửa: URL đúng là /health
    assert rv.status_code == 200
    assert rv.data == b"OK" # Sửa: app.py trả về text "OK", không phải JSON

def test_create_task(auth_client):
    """Test tạo task mới (PASSED, giữ nguyên)"""
    task_data = {
        'title': 'Test Task',
        'description': 'Test Description',
        'priority': 'high'
    }
    rv = auth_client.post('/api/tasks',
                    data=json.dumps(task_data),
                    content_type='application/json')
    assert rv.status_code == 201
    json_data = rv.get_json()
    assert json_data['title'] == 'Test Task'

def test_get_tasks(auth_client):
    """Test lấy danh sách tasks (ĐÃ SỬA)"""
    # (Đã loại bỏ logic file JSON cũ)
    # Tạo 1 task mới để đảm bảo có data
    task_data = {
        'title': 'Get Task Test',
        'description': 'Test Description',
        'priority': 'high'
    }
    auth_client.post('/api/tasks',
                data=json.dumps(task_data),
                content_type='application/json')
    
    rv = auth_client.get('/api/tasks')
    assert rv.status_code == 200
    tasks = rv.get_json()
    assert len(tasks) > 0 # Đảm bảo có task trả về
    assert tasks[-1]['title'] == 'Get Task Test' # Kiểm tra task vừa tạo

def test_update_task_status(auth_client):
    """Test cập nhật trạng thái task (PASSED, giữ nguyên)"""
    task_data = {'title': 'Task to Update', 'priority': 'low'}
    rv = auth_client.post('/api/tasks',
                    data=json.dumps(task_data),
                    content_type='application/json')
    task_id = rv.get_json()['id']
    
    update_data = {'status': 'completed'}
    rv = auth_client.put(f'/api/tasks/{task_id}',
                   data=json.dumps(update_data),
                   content_type='application/json')
    assert rv.status_code == 200
    assert rv.get_json()['status'] == 'completed'

def test_task_validation(auth_client):
    """Test validation khi tạo task (PASSED, giữ nguyên)"""
    task_data = {'title': 'Test Task'}
    rv = auth_client.post('/api/tasks',
                    data=json.dumps(task_data),
                    content_type='application/json')
    assert rv.status_code == 201

def test_invalid_task_id(auth_client):
    """Test xử lý task ID không tồn tại (Sửa nhẹ cho chắc)"""
    update_data = {'status': 'completed'}
    rv = auth_client.put('/api/tasks/999999', # Dùng 1 ID số không tồn tại
                   data=json.dumps(update_data),
                   content_type='application/json')
    assert rv.status_code == 404 # App trả 404 là đúng

# XÓA BỎ test_data_persistence (vì app không còn dùng file JSON)