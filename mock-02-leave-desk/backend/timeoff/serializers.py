def employee_to_dict(employee):
    return {
        "id": employee.id,
        "name": employee.name,
        "username": employee.username,
        "department": employee.department,
        "balance_days": employee.balance_days,
    }


def leave_to_dict(leave):
    return {
        "id": leave.id,
        "employee_id": leave.employee_id,
        "employee_name": leave.employee.name,
        "department": leave.employee.department,
        "leave_type": leave.leave_type,
        "start_date": leave.start_date.isoformat(),
        "end_date": leave.end_date.isoformat(),
        "days": leave.days,
        "reason": leave.reason,
        "status": leave.status,
        "created_by": leave.created_by,
        "decided_by": leave.decided_by,
        "decided_at": leave.decided_at.isoformat() if leave.decided_at else None,
        "created_at": leave.created_at.isoformat(),
    }
