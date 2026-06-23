# routes/offer_routes.py

from flask import Blueprint, jsonify, request

from models import db, OfferCatalogue

offer_bp = Blueprint(
    "offers",
    __name__,
    url_prefix="/api/offers"
)


@offer_bp.route("", methods=["GET"])
def get_offers():
    """
    Retrieve all active offer catalogues.
    """

    offers = OfferCatalogue.query.filter_by(active=1).order_by(
        OfferCatalogue.name_de.asc()
    ).all()

    return jsonify([
        {
            "id": offer.id,
            "name_de": offer.name_de,
            "name_en": offer.name_en,
            "description_de": offer.description_de,
            "description_en": offer.description_en,
            "pdf_url": offer.pdf_url,
            "price": float(offer.price) if offer.price else None,
            "active": offer.active
        }
        for offer in offers
    ])


@offer_bp.route("/<int:offer_id>", methods=["GET"])
def get_offer(offer_id):
    """
    Retrieve a single offer catalogue by identifier.
    """

    offer = OfferCatalogue.query.get(offer_id)

    if not offer:
        return jsonify({
            "success": False,
            "message": "Offer catalogue not found."
        }), 404

    return jsonify({
        "id": offer.id,
        "name_de": offer.name_de,
        "name_en": offer.name_en,
        "description_de": offer.description_de,
        "description_en": offer.description_en,
        "pdf_url": offer.pdf_url,
        "price": float(offer.price) if offer.price else None,
        "active": offer.active
    })


@offer_bp.route("", methods=["POST"])
def create_offer():
    """
    Create a new offer catalogue.
    """

    data = request.get_json()

    offer = OfferCatalogue(
        name_de=data["name_de"],
        name_en=data["name_en"],
        description_de=data.get("description_de"),
        description_en=data.get("description_en"),
        pdf_url=data.get("pdf_url"),
        price=data.get("price"),
        active=data.get("active", 1)
    )

    db.session.add(offer)
    db.session.commit()

    return jsonify({
        "success": True,
        "offer_id": offer.id
    }), 201


@offer_bp.route("/<int:offer_id>", methods=["PUT"])
def update_offer(offer_id):
    """
    Update an existing offer catalogue.
    """

    offer = OfferCatalogue.query.get(offer_id)

    if not offer:
        return jsonify({
            "success": False,
            "message": "Offer catalogue not found."
        }), 404

    data = request.get_json()

    offer.name_de = data.get("name_de", offer.name_de)
    offer.name_en = data.get("name_en", offer.name_en)
    offer.description_de = data.get(
        "description_de",
        offer.description_de
    )
    offer.description_en = data.get(
        "description_en",
        offer.description_en
    )
    offer.pdf_url = data.get("pdf_url", offer.pdf_url)
    offer.price = data.get("price", offer.price)
    offer.active = data.get("active", offer.active)

    db.session.commit()

    return jsonify({
        "success": True,
        "offer_id": offer.id
    })


@offer_bp.route("/<int:offer_id>", methods=["DELETE"])
def delete_offer(offer_id):
    """
    Deactivate an offer catalogue.

    The record is not physically deleted. It is only marked
    as inactive to keep historical reservation data valid.
    """

    offer = OfferCatalogue.query.get(offer_id)

    if not offer:
        return jsonify({
            "success": False,
            "message": "Offer catalogue not found."
        }), 404

    offer.active = 0
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Offer catalogue deactivated."
    })
