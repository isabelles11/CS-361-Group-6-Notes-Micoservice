import requests
import json

BASE_URL = "http://127.0.0.1:5004"


def print_title(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def print_response(response):
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)


def main():
    user_id = "isabelle"
    other_user = "another_user"
    item_type = "task"
    item_id = "t1"

    # 1. Add note
    print_title("1. Add a valid note")
    add_payload = {
        "user_id": user_id,
        "item_type": item_type,
        "item_id": item_id,
        "text": "Remember to submit this before midnight.",
        "idempotency_key": "demo-note-001"
    }
    response = requests.post(f"{BASE_URL}/notes/add", json=add_payload)
    print_response(response)

    note_id = None
    if response.status_code in (200, 201):
        note_id = response.json()["data"]["note_id"]

    # 2. Try idempotent retry
    print_title("2. Retry same add request with same idempotency key")
    response = requests.post(f"{BASE_URL}/notes/add", json=add_payload)
    print_response(response)

    # 3. List notes
    print_title("3. List notes for item")
    response = requests.get(
        f"{BASE_URL}/notes/list",
        params={
            "user_id": user_id,
            "item_type": item_type,
            "item_id": item_id
        }
    )
    print_response(response)

    # 4. Edit note
    if note_id:
        print_title("4. Edit the note")
        edit_payload = {
            "user_id": user_id,
            "text": "Updated note: submit this tonight and double-check formatting."
        }
        response = requests.put(f"{BASE_URL}/notes/edit/{note_id}", json=edit_payload)
        print_response(response)

    # 5. Unauthorized edit
    if note_id:
        print_title("5. Unauthorized edit attempt by another user")
        bad_edit_payload = {
            "user_id": other_user,
            "text": "I should not be able to edit this."
        }
        response = requests.put(f"{BASE_URL}/notes/edit/{note_id}", json=bad_edit_payload)
        print_response(response)

    # 6. Invalid short note
    print_title("6. Add invalid short note")
    short_note_payload = {
        "user_id": user_id,
        "item_type": item_type,
        "item_id": item_id,
        "text": "ok"
    }
    response = requests.post(f"{BASE_URL}/notes/add", json=short_note_payload)
    print_response(response)

    # 7. Delete note
    if note_id:
        print_title("7. Delete the note")
        delete_payload = {
            "user_id": user_id
        }
        response = requests.delete(f"{BASE_URL}/notes/delete/{note_id}", json=delete_payload)
        print_response(response)

    # 8. List notes again after delete
    print_title("8. List notes again after delete")
    response = requests.get(
        f"{BASE_URL}/notes/list",
        params={
            "user_id": user_id,
            "item_type": item_type,
            "item_id": item_id
        }
    )
    print_response(response)


if __name__ == "__main__":
    main()