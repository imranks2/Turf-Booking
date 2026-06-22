from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.extensions import Base, db_session, engine
from app.models.booking import (
    Booking,
    BookingStatus,
    Payment,
    PaymentStatus,
    PaymentType,
)
from app.models.slot import Slot, SlotStatus
from app.models.sport import Sport, TurfSport
from app.models.turf import Turf
from app.models.user import (
    KycStatus,
    Player,
    SaasAdminProfile,
    SubscriptionStatus,
    TurfOwnerProfile,
    User,
    UserRole,
)
from app.schemas.turf import TurfCreateSchema, TurfSportCreateSchema
from app.services import auth_service, payment_service, turf_service
from app.utils.helpers import generate_booking_code

ADMIN_PASSWORD = "Admin@12345"
OWNER_PASSWORD = "Owner@12345"
PLAYER_PASSWORD = "Player@12345"

FULL_WEEK = {
    day: {"open": "06:00", "close": "23:00"}
    for day in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
}


def _get_or_create_user(email: str, phone: str, password: str, role: UserRole, is_active: bool) -> tuple[User, bool]:
    user = db_session.scalar(select(User).where(User.email == email))
    if user:
        return user, False
    user = User(
        email=email,
        phone=phone,
        password_hash=auth_service.hash_password(password),
        role=role,
        is_active=is_active,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user, True


def _ensure_admin() -> User:
    user, created = _get_or_create_user(
        "admin@turfapp.in", "+919800000001", ADMIN_PASSWORD, UserRole.saas_admin, True
    )
    if created:
        db_session.add(
            SaasAdminProfile(user_id=user.id, name="Platform Admin", permissions_json={"all": True})
        )
    db_session.commit()
    return user


def _ensure_owner(email: str, phone: str, business_name: str) -> User:
    user, created = _get_or_create_user(email, phone, OWNER_PASSWORD, UserRole.turf_owner, True)
    if created:
        db_session.add(
            TurfOwnerProfile(
                user_id=user.id,
                business_name=business_name,
                gst_number="27ABCDE1234F1Z5",
                bank_account_number="000111222333",
                bank_ifsc="HDFC0000123",
                razorpay_contact_id="cont_demo",
                razorpay_fund_account_id="fa_demo",
                payout_method="bank_account",
                kyc_status=KycStatus.verified,
                subscription_status=SubscriptionStatus.active,
                subscription_expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            )
        )
    db_session.commit()
    return user


def _ensure_player(email: str, phone: str, name: str, city: str) -> User:
    user, created = _get_or_create_user(email, phone, PLAYER_PASSWORD, UserRole.player, True)
    if created:
        db_session.add(
            Player(
                user_id=user.id,
                name=name,
                phone=phone,
                city=city,
                preferred_sports=["Football", "Cricket"],
            )
        )
    db_session.commit()
    return user


def _ensure_turf(owner_id: str, spec: dict) -> Turf:
    turf = db_session.scalar(
        select(Turf).where(Turf.tenant_id == owner_id, Turf.name == spec["name"])
    )
    if turf:
        return turf
    return turf_service.create_turf(
        db_session,
        owner_id,
        TurfCreateSchema(
            name=spec["name"],
            address=spec["address"],
            city=spec["city"],
            latitude=spec["latitude"],
            longitude=spec["longitude"],
            description=spec["description"],
            amenities=spec["amenities"],
            operating_hours=FULL_WEEK,
        ),
        [],
    )


def _ensure_turf_sport(owner_id: str, turf_id: str, sport_name: str, price: float, deposit: int) -> TurfSport:
    sport = db_session.scalar(
        select(Sport).where(Sport.tenant_id == owner_id, Sport.name == sport_name)
    )
    if sport:
        existing = db_session.scalar(
            select(TurfSport).where(
                TurfSport.turf_id == turf_id, TurfSport.sport_id == sport.id
            )
        )
        if existing:
            return existing
    return turf_service.add_turf_sport(
        db_session,
        owner_id,
        turf_id,
        TurfSportCreateSchema(
            sport_name=sport_name,
            price_per_hour=price,
            advance_deposit_percentage=deposit,
            min_players=2,
            max_players=22,
        ),
    )


def _ensure_demo_booking(owner_id: str, player: Player, turf_sport: TurfSport) -> None:
    if db_session.scalar(select(Booking).where(Booking.booking_code == "DEMOBOOK")):
        return

    target_date = date.today() + timedelta(days=3)
    slots = list(
        db_session.scalars(
            select(Slot)
            .where(
                Slot.turf_sport_id == turf_sport.id,
                Slot.slot_date == target_date,
                Slot.status == SlotStatus.available,
            )
            .order_by(Slot.start_time)
            .limit(2)
        )
    )
    if len(slots) < 2:
        return

    pricing = payment_service.compute_pricing(
        Decimal(turf_sport.price_per_hour), Decimal(2), turf_sport.advance_deposit_percentage
    )
    booking = Booking(
        tenant_id=owner_id,
        booking_code="DEMOBOOK",
        player_id=player.id,
        turf_sport_id=turf_sport.id,
        slot_ids=sorted(s.id for s in slots),
        booking_date=target_date,
        total_amount=pricing["total_price"],
        advance_deposit_amount=pricing["advance_deposit_amount"],
        platform_fee=pricing["platform_fee"],
        owner_payout_amount=pricing["owner_payout_amount"],
        status=BookingStatus.confirmed,
        payment_status=PaymentStatus.captured,
        razorpay_order_id="order_demo",
        razorpay_payment_id="pay_demo",
    )
    db_session.add(booking)
    db_session.flush()
    for slot in slots:
        slot.status = SlotStatus.booked
        slot.booking_id = booking.id
    db_session.add_all(
        [
            Payment(
                tenant_id=owner_id,
                booking_id=booking.id,
                amount=pricing["payable_now"],
                type=PaymentType.advance,
                razorpay_order_id="order_demo",
                razorpay_payment_id="pay_demo",
                status=PaymentStatus.captured,
            ),
            Payment(
                tenant_id=owner_id,
                booking_id=booking.id,
                amount=pricing["owner_payout_amount"],
                type=PaymentType.payout,
                status=PaymentStatus.pending,
            ),
        ]
    )
    db_session.commit()


TURFS = [
    {
        "owner": ("owner1@turfapp.in", "+919800000002", "Greenfield Sports Pvt Ltd"),
        "turf": {
            "name": "Greenfield Turf Arena",
            "address": "Baner Road, Baner",
            "city": "Pune",
            "latitude": 18.5590,
            "longitude": 73.7868,
            "description": "Premium 5-a-side and 7-a-side football turf with floodlights.",
            "amenities": ["parking", "washroom", "floodlights", "drinking_water"],
        },
        "sports": [("Football", 1200.0, 50), ("Cricket", 1500.0, 40)],
    },
    {
        "owner": ("owner2@turfapp.in", "+919800000003", "Urban Kickz LLP"),
        "turf": {
            "name": "Urban Kickz Box Cricket",
            "address": "Andheri West, Link Road",
            "city": "Mumbai",
            "latitude": 19.1351,
            "longitude": 72.8270,
            "description": "Indoor box cricket and badminton courts in the heart of Andheri.",
            "amenities": ["parking", "washroom", "cafeteria", "first_aid"],
        },
        "sports": [("Cricket", 1800.0, 50), ("Badminton", 600.0, 50)],
    },
]


def run() -> None:
    Base.metadata.create_all(engine)

    admin = _ensure_admin()
    player = _ensure_player("player@turfapp.in", "+919800000010", "Demo Player", "Pune")
    player_profile = db_session.scalar(select(Player).where(Player.user_id == player.id))

    first_turf_sport: TurfSport | None = None
    first_owner_id: str | None = None

    for entry in TURFS:
        email, phone, business = entry["owner"]
        owner = _ensure_owner(email, phone, business)
        turf = _ensure_turf(owner.id, entry["turf"])
        for sport_name, price, deposit in entry["sports"]:
            ts = _ensure_turf_sport(owner.id, turf.id, sport_name, price, deposit)
            turf_service.generate_slots(db_session, owner.id, ts.id, days=14)
            if first_turf_sport is None:
                first_turf_sport = ts
                first_owner_id = owner.id

    if first_turf_sport and player_profile and first_owner_id:
        _ensure_demo_booking(first_owner_id, player_profile, first_turf_sport)

    db_session.remove()

    print("\n=== Demo data seeded ===")
    print(f"{'Role':<12}{'Email':<26}{'Password'}")
    print(f"{'-' * 50}")
    print(f"{'saas_admin':<12}{'admin@turfapp.in':<26}{ADMIN_PASSWORD}")
    print(f"{'turf_owner':<12}{'owner1@turfapp.in':<26}{OWNER_PASSWORD}")
    print(f"{'turf_owner':<12}{'owner2@turfapp.in':<26}{OWNER_PASSWORD}")
    print(f"{'player':<12}{'player@turfapp.in':<26}{PLAYER_PASSWORD}")
    print("\n2 turfs, 4 turf-sports, 14 days of slots, 1 confirmed demo booking (code DEMOBOOK).")


if __name__ == "__main__":
    run()
