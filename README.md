Overview

The Notes / Comments Microservice allows users to create, view, edit, and delete notes attached to items in the main application. These notes give users a place to save extra context, reminders, or comments for different item types such as games, medications, or tasks.

This microservice was built with Flask and stores its data in local JSON files. It supports validation, soft deletion, standardized JSON responses, and simple ownership checks so users can only manage their own notes.

Features

This microservice supports the following actions:

Add a note to an item

List notes for a specific item

Edit an existing note

Soft delete a note

Validate that the referenced item exists in items.json

Return standardized success/error JSON responses

Technologies Used

Python 3

Flask

JSON file storage

UUID for unique note IDs

UTC timestamps using datetime

Project Structure
Notes Microservice/
├── notes_microservice.py
├── notes.json
├── items.json
└── README.md


If your file is not literally named app.py, replace that filename in this README with the real one.

File Descriptions

notes_microservice.py
Main Flask microservice file. Contains all routes, validation, helper functions, and startup logic.

notes.json
Stores note records created by the microservice.

items.json
Stores valid item references for game, med, and task.

README.md
Documentation for how the microservice works.

How to Run the Microservice
1. Go into the project folder
cd "Notes Microservice"

2. Install Flask if needed
pip install flask

3. Run the microservice
python3 app.py


The service will start on:

http://127.0.0.1:5004


If notes.json does not exist yet, the program creates it automatically.
If items.json does not exist yet, the program creates a sample one automatically.

Base URL
http://127.0.0.1:5004

Communication Contract

This microservice communicates through HTTP requests and JSON responses.

Endpoints
1. Home Route

GET /

Used to verify that the microservice is running.

Example Request
GET /

Example Response
{
  "message": "Notes/Comments Microservice is running."
}

2. Add Note

POST /notes/add

Creates a new note linked to a valid item.

Request Body
{
  "user_id": "user123",
  "item_type": "med",
  "item_id": "m1",
  "text": "Take this after breakfast",
  "idempotency_key": "abc123"
}

Success Response
{
  "success": true,
  "data": {
    "note_id": "generated-uuid",
    "user_id": "user123",
    "item_type": "med",
    "item_id": "m1",
    "text": "Take this after breakfast",
    "schema_version": "1.0",
    "created_at": "2026-03-14T12:00:00+00:00",
    "updated_at": "2026-03-14T12:00:00+00:00",
    "deleted_at": null,
    "idempotency_key": "abc123"
  }
}

Notes

user_id is required

item_type must be one of:

game

med

task

item_id must exist in items.json

text must be at least 3 characters long

idempotency_key is optional but recommended

If the same user sends the same idempotency key again, the microservice returns the existing note instead of creating a duplicate

3. List Notes

GET /notes/list

Returns all visible notes for a specific item, sorted by most recent first.

Query Parameters

user_id

item_type

item_id

Example Request
GET /notes/list?user_id=user123&item_type=med&item_id=m1

Success Response
{
  "success": true,
  "data": [
    {
      "note_id": "uuid-1",
      "user_id": "user123",
      "item_type": "med",
      "item_id": "m1",
      "text": "Take this after breakfast",
      "schema_version": "1.0",
      "created_at": "2026-03-14T12:00:00+00:00",
      "updated_at": "2026-03-14T12:00:00+00:00",
      "deleted_at": null,
      "idempotency_key": "abc123"
    }
  ]
}

4. Edit Note

PUT /notes/edit/<note_id>

Updates the text of an existing note if the requesting user owns it.

Example Request
PUT /notes/edit/uuid-1

Request Body
{
  "user_id": "user123",
  "text": "Updated note text"
}

Success Response
{
  "success": true,
  "data": {
    "note_id": "uuid-1",
    "user_id": "user123",
    "item_type": "med",
    "item_id": "m1",
    "text": "Updated note text",
    "schema_version": "1.0",
    "created_at": "2026-03-14T12:00:00+00:00",
    "updated_at": "2026-03-14T12:10:00+00:00",
    "deleted_at": null,
    "idempotency_key": "abc123"
  }
}

Rules

Only the owner of the note can edit it

New text must be at least 3 characters long

Deleted notes cannot be edited

5. Delete Note

DELETE /notes/delete/<note_id>

Soft deletes a note if the requesting user owns it.

Example Request
DELETE /notes/delete/uuid-1

Request Body
{
  "user_id": "user123"
}

Success Response
{
  "success": true,
  "data": {
    "message": "Note deleted successfully.",
    "note_id": "uuid-1",
    "deleted_at": "2026-03-14T12:15:00+00:00"
  }
}

Rules

Only the owner of the note can delete it

This is a soft delete

The note is not removed from notes.json, but its deleted_at field is updated

Deleted notes no longer appear in note listings

Error Response Format

The microservice uses a consistent error format:

{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "user_id is required."
  }
}

Possible Error Codes

BAD_REQUEST

VALIDATION_ERROR

ITEM_NOT_FOUND

NOTE_NOT_FOUND

AUTHORIZATION_ERROR

Data Storage
notes.json

This file stores all note objects.

Example note:

{
  "note_id": "uuid-value",
  "user_id": "user123",
  "item_type": "med",
  "item_id": "m1",
  "text": "Take after breakfast",
  "schema_version": "1.0",
  "created_at": "2026-03-14T12:00:00+00:00",
  "updated_at": "2026-03-14T12:00:00+00:00",
  "deleted_at": null,
  "idempotency_key": "abc123"
}

items.json

This file stores valid item IDs that notes are allowed to reference.

Example:

{
  "game": ["g1", "g2"],
  "med": ["m1", "m2"],
  "task": ["t1", "t2"]
}

Validation Rules

The microservice enforces the following rules:

user_id must be provided

item_type must be game, med, or task

item_id must exist in items.json

note text must be at least 3 characters long

users can only edit or delete their own notes

Quality Attributes
Security / Privacy

Notes are user-specific. A user cannot edit or delete another user’s notes.

Validation

Incoming data is checked before processing, and invalid requests return standardized error messages.

Maintainability

The code is separated into helper functions and route handlers, making it easier to update and understand.

Consistency

Responses follow a standardized success/error JSON format.

Data Integrity

The service verifies item references before linking notes to items.
