from flask import Blueprint
from flask import jsonify
from flask import request

from models import Customer

customer_bp = Blueprint(
    "customers",
    __name__,
    url_prefix="/api/customers"
)


@customer_bp.route("", methods=["GET"])
def get_customers():
    """
    Retrieve all customers.

    Returns:
        list:
            List of customer records.
    """

    customers = Customer.query.order_by(
        Customer.created_at.desc()
    ).all()

    return jsonify([
        {
            "id": customer.id,
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "created_at": (
                customer.created_at.isoformat()
                if customer.created_at
                else None
            )
        }
        for customer in customers
    ])


@customer_bp.route("/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    """
    Retrieve a customer by identifier.

    Args:
        customer_id (int):
            Customer identifier.

    Returns:
        dict:
            Customer details.
    """

    customer = Customer.query.get(customer_id)

    if not customer:
        return jsonify({
            "success": False,
            "message": "Customer not found."
        }), 404

    return jsonify({
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "created_at": (
            customer.created_at.isoformat()
            if customer.created_at
            else None
        )
    })


@customer_bp.route("", methods=["POST"])
def create_customer():
    """
    Create a new customer.

    Expected payload:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+49123456789"
    }

    Returns:
        dict:
            Created customer information.
    """

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")

    if not name:
        return jsonify({
            "success": False,
            "message": "Name is required."
        }), 400

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400

    existing_customer = Customer.query.filter_by(
        email=email
    ).first()

    if existing_customer:
        return jsonify({
            "success": False,
            "message": "Customer already exists."
        }), 409

    customer = Customer(
        name=name,
        email=email,
        phone=phone
    )

    from models import db

    db.session.add(customer)
    db.session.commit()

    return jsonify({
        "success": True,
        "customer_id": customer.id
    }), 201


@customer_bp.route(
    "/<int:customer_id>",
    methods=["PUT"]
)
def update_customer(customer_id):
    """
    Update an existing customer.

    Args:
        customer_id (int):
            Customer identifier.

    Expected payload:
    {
        "name": "John Doe",
        "phone": "+49123456789"
    }

    Returns:
        dict:
            Updated customer information.
    """

    customer = Customer.query.get(customer_id)

    if not customer:
        return jsonify({
            "success": False,
            "message": "Customer not found."
        }), 404

    data = request.get_json()

    customer.name = data.get(
        "name",
        customer.name
    )

    customer.phone = data.get(
        "phone",
        customer.phone
    )

    from models import db

    db.session.commit()

    return jsonify({
        "success": True,
        "customer_id": customer.id
    })


@customer_bp.route(
    "/<int:customer_id>",
    methods=["DELETE"]
)
def delete_customer(customer_id):
    """
    Delete a customer.

    A customer should only be deleted if no
    business records depend on it.

    Args:
        customer_id (int):
            Customer identifier.

    Returns:
        dict:
            Deletion result.
    """

    customer = Customer.query.get(customer_id)

    if not customer:
        return jsonify({
            "success": False,
            "message": "Customer not found."
        }), 404

    from models import db

    db.session.delete(customer)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Customer deleted."
    })


@customer_bp.route(
    "/<int:customer_id>/reservations",
    methods=["GET"]
)
def get_customer_reservations(customer_id):
    """
    Retrieve all reservations belonging
    to a specific customer.

    Args:
        customer_id (int):
            Customer identifier.

    Returns:
        list:
            Customer reservations.
    """

    customer = Customer.query.get(customer_id)

    if not customer:
        return jsonify({
            "success": False,
            "message": "Customer not found."
        }), 404

    reservations = customer.reservations

    return jsonify([
        {
            "id": reservation.id,
            "reservation_number": (
                reservation.reservation_number
            ),
            "status_code": (
                reservation.status_code
            ),
            "event_type_code": (
                reservation.event_type_code
            ),
            "created_at": (
                reservation.created_at.isoformat()
                if reservation.created_at
                else None
            )
        }
        for reservation in reservations
    ])
