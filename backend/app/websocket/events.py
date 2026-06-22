from __future__ import annotations

from flask_socketio import emit, join_room

from app.extensions import db_session, socketio
from app.models.slot import Slot, SlotStatus
from app.utils import redis_client as rc


def _turf_room(turf_id: str) -> str:
    return f"turf_{turf_id}"


def _slot_room(turf_sport_id: str, slot_date: str) -> str:
    return f"slot_{turf_sport_id}_{slot_date}"


def _slot_room_for(slot: Slot) -> str:
    return _slot_room(slot.turf_sport_id, slot.slot_date.isoformat())


def register_socket_handlers() -> None:
    @socketio.on("connect")
    def _on_connect():
        return True

    @socketio.on("disconnect")
    def _on_disconnect():
        return None

    @socketio.on("join_turf_room")
    def _join_turf_room(data: dict):
        turf_id = (data or {}).get("turf_id")
        if turf_id:
            join_room(_turf_room(turf_id))

    @socketio.on("join_slot_room")
    def _join_slot_room(data: dict):
        data = data or {}
        turf_sport_id = data.get("turf_sport_id")
        slot_date = data.get("date")
        if turf_sport_id and slot_date:
            join_room(_slot_room(turf_sport_id, slot_date))

    @socketio.on("lock_slot")
    def _lock_slot(data: dict):
        data = data or {}
        slot_id = data.get("slot_id")
        player_id = data.get("player_id")
        if not slot_id or not player_id:
            emit("booking_conflict", {"slot_id": slot_id, "reason": "invalid_request"})
            return
        slot = db_session.get(Slot, slot_id)
        if not slot or slot.status != SlotStatus.available:
            emit("booking_conflict", {"slot_id": slot_id, "reason": "unavailable"})
            return
        if not rc.acquire_slot_lock(slot_id, player_id):
            emit("booking_conflict", {"slot_id": slot_id, "reason": "locked"})
            return
        emit(
            "slot_locked",
            {"slot_id": slot_id, "player_id": player_id},
            to=_slot_room_for(slot),
        )

    @socketio.on("unlock_slot")
    def _unlock_slot(data: dict):
        data = data or {}
        slot_id = data.get("slot_id")
        player_id = data.get("player_id")
        if not slot_id:
            return
        if rc.get_slot_lock_owner(slot_id) != player_id:
            emit("booking_conflict", {"slot_id": slot_id, "reason": "not_lock_owner"})
            return
        rc.release_slot_lock(slot_id)
        slot = db_session.get(Slot, slot_id)
        if slot:
            emit("slot_unlocked", {"slot_id": slot_id}, to=_slot_room_for(slot))

    @socketio.on("block_slot")
    def _block_slot(data: dict):
        data = data or {}
        slot_id = data.get("slot_id")
        reason = data.get("reason")
        owner_id = data.get("owner_id")
        if not slot_id:
            return
        slot = db_session.get(Slot, slot_id)
        if not slot or (owner_id and slot.tenant_id != owner_id):
            emit("booking_conflict", {"slot_id": slot_id, "reason": "forbidden"})
            return
        slot.status = SlotStatus.blocked
        slot.blocked_reason = reason
        db_session.commit()
        rc.release_slot_lock(slot_id)
        emit(
            "slot_blocked",
            {"slot_id": slot_id, "reason": reason},
            to=_slot_room_for(slot),
        )
