from flask import Blueprint, render_template
from models.attendance import Attendance
from utils.decorators import login_required, permission_required

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


@attendance_bp.route('/')
@login_required
@permission_required('attendance_read')
def attendance_dashboard():
    """Dashboard de asistencia automática"""
    today_attendance = Attendance.get_today_actions()

    return render_template(
        'attendance/register.html',
        today_attendance=today_attendance
    )