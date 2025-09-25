from fastapi import APIRouter
from .database import database
from .models import notes
from .schemas import NoteIn, NoteOut

router = APIRouter(prefix="/notes", tags=["notes"])

@router.post("/", response_model=NoteOut)
async def create_note(note: NoteIn):
    note_id = await database.execute(notes.insert().values(**note.model_dump()))
    return {**note.model_dump(), "id": note_id}

@router.get("/{note_id}", response_model=NoteOut)
async def read_note(note_id: int):
    query = notes.select().where(notes.c.id == note_id)
    note = await database.fetch_one(query)
    return note

@router.get("/", response_model=list[NoteOut])
async def list_notes():
    return await database.fetch_all(notes.select())