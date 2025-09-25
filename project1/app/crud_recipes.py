from fastapi import APIRouter
from .database import database
from .models import recipes
from .schemas import RecipeIn, RecipeOut

router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.post("/", response_model=RecipeOut)
async def create_recipe(recipe: RecipeIn):
    recipe_id = await database.execute(recipes.insert().values(**recipe.model_dump()))
    return {**recipe.model_dump(), "id": recipe_id}

@router.get("/{recipe_id}", response_model=RecipeOut)
async def read_recipe(recipe_id: int):
    query = recipes.select().where(recipes.c.id == recipe_id)
    return await database.fetch_one(query)

@router.get("/", response_model=list[RecipeOut])
async def list_recipes():
    return await database.fetch_all(recipes.select())
