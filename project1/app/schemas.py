from pydantic import BaseModel

# notes
class NoteIn(BaseModel):
    title: str
    content: str

class NoteOut(NoteIn):
    id: int

# recipes
class RecipeIn(BaseModel):
    rcp_seq: str
    rcp_nm: str
    rcp_way2: str
    rcp_pat2: str
    info_eng: float
    info_car: float
    info_pro: float
    info_fat: float
    info_na: float
    rcp_parts_dtls: str
    recipe_steps: str
    rcp_na_tip: str | None = None
    hash_tag: str | None = None

class RecipeOut(RecipeIn):
    id: int