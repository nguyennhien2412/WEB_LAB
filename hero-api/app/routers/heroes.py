from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import select
from app.database import SessionDep
from app.models import Hero, HeroCreate, HeroPublic, HeroUpdate, Team

router = APIRouter(prefix="/heroes", tags=["heroes"])
NOT_FOUND = {404: {"description": "Hero not found"}}

def ensure_team_exists(session, team_id: int | None):
    if team_id is not None and not session.get(Team, team_id):
        # Đổi thành lỗi 400 theo chuẩn của thầy
        raise HTTPException(status_code=400, detail=f"Team {team_id} does not exist")

@router.post("", response_model=HeroPublic, status_code=status.HTTP_201_CREATED, 
             summary="Create a hero", responses={400: {"description": "Team does not exist"}})
def create_hero(hero_in: HeroCreate, session: SessionDep):
    ensure_team_exists(session, hero_in.team_id)
    hero = Hero.model_validate(hero_in)
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero

@router.get("", response_model=list[HeroPublic], summary="List heroes")
def list_heroes(
    session: SessionDep,
    offset: int = 0,
    limit: int = Query(default=10, ge=1, le=100), # Thêm ge=1
    min_age: int | None = None,
    team_id: int | None = None,
    name: str | None = None,
):
    statement = select(Hero)
    if min_age is not None:
        statement = statement.where(Hero.age >= min_age)
    if team_id is not None:
        statement = statement.where(Hero.team_id == team_id)
    if name:
        statement = statement.where(Hero.name.ilike(f"%{name}%"))
    statement = statement.order_by(Hero.id).offset(offset).limit(limit)
    return session.exec(statement).all()

@router.get("/{hero_id}", response_model=HeroPublic, summary="Get one hero", responses=NOT_FOUND)
def read_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

@router.patch("/{hero_id}", response_model=HeroPublic, summary="Update a hero partially", 
              responses={**NOT_FOUND, 400: {"description": "Team does not exist"}})
def update_hero(hero_id: int, hero_in: HeroUpdate, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    data = hero_in.model_dump(exclude_unset=True)
    ensure_team_exists(session, data.get("team_id"))
    hero.sqlmodel_update(data)
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero

@router.delete("/{hero_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a hero")
def delete_hero(hero_id: int, session: SessionDep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()