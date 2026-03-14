from flask import Flask, request, jsonify
import json
import os
import uuid
from datetime import datetime, timezone

app = Flask(__name__)

NOTES_FILE = "notes.json"
ITEMS_FILE = "items.json"

VALID_ITEM_TYPES = {"game", "med", "task"}
MIN_NOTE_LENGTH = 3
SCHEMA_VERSION = "1.0"


# -----------------------------
# Helper functions
# -----------------------------
def now_iso() -> str:
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def load_json_file(filename: str, default):
    """Load JSON data from a file. Return default if file does not exist."""
    if not os.path.exists(filename):
        return default

    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return default


def save_json_file(filename: str, data) -> None:
    """Save JSON data to a file."""
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def error_response(status_code: int, error_code: str, message: str):
    """Standardized error response."""
    return jsonify({
        "success": False,
        "error": {
            "code": error_code,
            "message": message
        }
    }), status_code


def success_response(data, status_code: int = 200):
    """Standardized success response."""
    return jsonify({
        "success": True,
        "data": data
    }), status_code


def validate_item_reference(item_type: str, item_id: str) -> bool:
    """
    Check if item exists in items.json.
    Expected items.json format:
    {
      "game": ["g1", "g2"],
      "med": ["m1"],
      "task": ["t1", "t2"]
    }
    """
    items = load_json_file(ITEMS_FILE, {"game": [], "med": [], "task": []})
    return item_type in items and item_id in items[item_type]


def load_notes():
    return load_json_file(NOTES_FILE, [])


def save_notes(notes):
    save_json_file(NOTES_FILE, notes)


def find_note_by_id(note_id: str, notes: list):
    for note in notes:
        if note["note_id"] == note_id:
            return note
    return None


def note_visible_to_user(note: dict, user_id: str) -> bool:
    return note["user_id"] == user_id and note["deleted_at"] is None


# -----------------------------
# Routes
# -----------------------------

@app.route("/notes/add", methods=["POST"])
def add_note():
    """
    Add a new note to an item.
    Required JSON:
    {
      "user_id": "user123",
      "item_type": "game",
      "item_id": "g1",
      "text": "Remember to finish this tonight",
      "idempotency_key": "abc123"   # optional but recommended
    }
    """
    data = request.get_json(silent=True)

    if not data:
        return error_response(400, "BAD_REQUEST", "Request body must be valid JSON.")

    user_id = str(data.get("user_id", "")).strip()
    item_type = str(data.get("item_type", "")).strip().lower()
    item_id = str(data.get("item_id", "")).strip()
    text = str(data.get("text", "")).strip()
    idempotency_key = str(data.get("idempotency_key", "")).strip()

    if not user_id:
        return error_response(400, "VALIDATION_ERROR", "user_id is required.")

    if item_type not in VALID_ITEM_TYPES:
        return error_response(
            400,
            "VALIDATION_ERROR",
            "item_type must be one of: game, med, task."
        )

    if not item_id:
        return error_response(400, "VALIDATION_ERROR", "item_id is required.")

    if len(text) < MIN_NOTE_LENGTH:
        return error_response(
            400,
            "VALIDATION_ERROR",
            f"Note text must be at least {MIN_NOTE_LENGTH} characters long."
        )

    if not validate_item_reference(item_type, item_id):
        return error_response(
            404,
            "ITEM_NOT_FOUND",
            "The referenced item could not be found or linked."
        )

    notes = load_notes()

    # Idempotency: if same user already used this key, return same note instead of making duplicate
    if idempotency_key:
        for note in notes:
            if (
                note.get("user_id") == user_id and
                note.get("idempotency_key") == idempotency_key
            ):
                return success_response(note, 200)

    timestamp = now_iso()

    new_note = {
        "note_id": str(uuid.uuid4()),
        "user_id": user_id,
        "item_type": item_type,
        "item_id": item_id,
        "text": text,
        "schema_version": SCHEMA_VERSION,
        "created_at": timestamp,
        "updated_at": timestamp,
        "deleted_at": None,
        "idempotency_key": idempotency_key if idempotency_key else None
    }

    notes.append(new_note)
    save_notes(notes)

    return success_response(new_note, 201)


@app.route("/notes/list", methods=["GET"])
def list_notes():
    """
    Get all notes for an item, most recent first.
    Query params:
    /notes/list?user_id=user123&item_type=game&item_id=g1
    """
    user_id = request.args.get("user_id", "").strip()
    item_type = request.args.get("item_type", "").strip().lower()
    item_id = request.args.get("item_id", "").strip()

    if not user_id:
        return error_response(400, "VALIDATION_ERROR", "user_id is required.")

    if item_type not in VALID_ITEM_TYPES:
        return error_response(
            400,
            "VALIDATION_ERROR",
            "item_type must be one of: game, med, task."
        )

    if not item_id:
        return error_response(400, "VALIDATION_ERROR", "item_id is required.")

    if not validate_item_reference(item_type, item_id):
        return error_response(
            404,
            "ITEM_NOT_FOUND",
            "The referenced item could not be found or linked."
        )

    notes = load_notes()

    matching_notes = [
        note for note in notes
        if note["user_id"] == user_id
        and note["item_type"] == item_type
        and note["item_id"] == item_id
        and note["deleted_at"] is None
    ]

    matching_notes.sort(key=lambda n: n["created_at"], reverse=True)

    return success_response(matching_notes, 200)


@app.route("/notes/edit/<note_id>", methods=["PUT"])
def edit_note(note_id):
    """
    Edit an existing note you own.
    Required JSON:
    {
      "user_id": "user123",
      "text": "Updated note text"
    }
    """
    data = request.get_json(silent=True)

    if not data:
        return error_response(400, "BAD_REQUEST", "Request body must be valid JSON.")

    user_id = str(data.get("user_id", "")).strip()
    new_text = str(data.get("text", "")).strip()

    if not user_id:
        return error_response(400, "VALIDATION_ERROR", "user_id is required.")

    if len(new_text) < MIN_NOTE_LENGTH:
        return error_response(
            400,
            "VALIDATION_ERROR",
            f"Note text must be at least {MIN_NOTE_LENGTH} characters long."
        )

    notes = load_notes()
    note = find_note_by_id(note_id, notes)

    if note is None or note["deleted_at"] is not None:
        return error_response(404, "NOTE_NOT_FOUND", "Note not found.")

    if note["user_id"] != user_id:
        return error_response(
            403,
            "AUTHORIZATION_ERROR",
            "You are not allowed to edit this note."
        )

    note["text"] = new_text
    note["updated_at"] = now_iso()

    save_notes(notes)
    return success_response(note, 200)


@app.route("/notes/delete/<note_id>", methods=["DELETE"])
def delete_note(note_id):
    """
    Soft delete a note you own.
    Required JSON:
    {
      "user_id": "user123"
    }
    """
    data = request.get_json(silent=True)

    if not data:
        return error_response(400, "BAD_REQUEST", "Request body must be valid JSON.")

    user_id = str(data.get("user_id", "")).strip()

    if not user_id:
        return error_response(400, "VALIDATION_ERROR", "user_id is required.")

    notes = load_notes()
    note = find_note_by_id(note_id, notes)

    if note is None or note["deleted_at"] is not None:
        return error_response(404, "NOTE_NOT_FOUND", "Note not found.")

    if note["user_id"] != user_id:
        return error_response(
            403,
            "AUTHORIZATION_ERROR",
            "You are not allowed to delete this note."
        )

    timestamp = now_iso()
    note["updated_at"] = timestamp
    note["deleted_at"] = timestamp

    save_notes(notes)

    return success_response({
        "message": "Note deleted successfully.",
        "note_id": note_id,
        "deleted_at": timestamp
    }, 200)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Notes/Comments Microservice is running."
    })


if __name__ == "__main__":
    # Creates notes file if missing
    if not os.path.exists(NOTES_FILE):
        save_notes([])

    # Creates sample items file if missing
    if not os.path.exists(ITEMS_FILE):
        sample_items = {
            "game": ["g1", "g2"],
            "med": ["m1", "m2"],
            "task": ["t1", "t2"]
        }
        save_json_file(ITEMS_FILE, sample_items)

    app.run(debug=True, port=5004)
