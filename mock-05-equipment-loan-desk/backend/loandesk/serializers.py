def loan_to_dict(loan):
    lines = loan.lines.select_related("equipment").order_by("id")
    return {
        "id": loan.id,
        "borrower": loan.borrower,
        "status": loan.status,
        "checked_out_on": loan.checked_out_on.isoformat(),
        "due_on": loan.due_on.isoformat(),
        "returned_on": loan.returned_on.isoformat() if loan.returned_on else None,
        "extensions": loan.extensions,
        "fee_cents": loan.fee_cents,
        "created_by": loan.created_by,
        "created_at": loan.created_at.isoformat(),
        "items": [
            {
                "equipment_id": line.equipment_id,
                "name": line.equipment.name,
                "category": line.equipment.category,
                "quantity": line.quantity,
            }
            for line in lines
        ],
    }
