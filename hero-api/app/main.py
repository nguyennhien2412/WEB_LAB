from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from sqlmodel import SQLModel, select
from sqlalchemy.exc import IntegrityError

from app.database import engine, SessionDep
from app import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/heroes", response_model=models.HeroPublic, status_code=201)
def create_hero(
    hero: models.HeroCreate,
    session: SessionDep,
):
    db_hero = models.Hero.model_validate(hero)

    if db_hero.team_id is not None:
        team = session.get(models.Team, db_hero.team_id)

        if not team:
            raise HTTPException(
                status_code=404,
                detail="Team not found",
            )

    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)

    return db_hero


@app.get("/heroes", response_model=list[models.HeroPublic])
def read_heroes(
    session: SessionDep,
    offset: int = 0,
    limit: int = Query(default=10, le=100),
    min_age: int | None = None,
    team_id: int | None = None,
    name: str | None = None,
):
    statement = select(models.Hero)

    if min_age is not None:
        statement = statement.where(
            models.Hero.age >= min_age
        )

    if team_id is not None:
        statement = statement.where(
            models.Hero.team_id == team_id
        )

    if name is not None:
        statement = statement.where(
            models.Hero.name.ilike(f"%{name}%")
        )

    statement = (
        statement
        .order_by(models.Hero.id)
        .offset(offset)
        .limit(limit)
    )

    heroes = session.exec(statement).all()

    return heroes


@app.get("/heroes/{hero_id}", response_model=models.HeroPublic)
def read_hero(
    hero_id: int,
    session: SessionDep,
):
    hero = session.get(models.Hero, hero_id)

    if not hero:
        raise HTTPException(
            status_code=404,
            detail="Hero not found",
        )

    return hero


@app.patch("/heroes/{hero_id}", response_model=models.HeroPublic)
def update_hero(
    hero_id: int,
    hero: models.HeroUpdate,
    session: SessionDep,
):
    db_hero = session.get(models.Hero, hero_id)

    if not db_hero:
        raise HTTPException(
            status_code=404,
            detail="Hero not found",
        )

    hero_data = hero.model_dump(exclude_unset=True)

    if (
        "team_id" in hero_data
        and hero_data["team_id"] is not None
    ):
        team = session.get(
            models.Team,
            hero_data["team_id"],
        )

        if not team:
            raise HTTPException(
                status_code=404,
                detail="Team not found",
            )

    db_hero.sqlmodel_update(hero_data)

    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)

    return db_hero


@app.delete("/heroes/{hero_id}", status_code=204)
def delete_hero(
    hero_id: int,
    session: SessionDep,
):
    hero = session.get(models.Hero, hero_id)

    if not hero:
        raise HTTPException(
            status_code=404,
            detail="Hero not found",
        )

    session.delete(hero)
    session.commit()

    return None

@app.post("/teams", response_model=models.TeamPublic, status_code=201)
def create_team(
    team_in: models.TeamCreate,
    session: SessionDep,
):
    team = models.Team.model_validate(team_in)

    session.add(team)

    try:
        session.commit()
        session.refresh(team)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Team already exists",
        )

    return team


@app.get("/teams", response_model=list[models.TeamPublic])
def read_teams(session: SessionDep):
    teams = session.exec(
        select(models.Team).order_by(models.Team.id)
    ).all()

    return teams


@app.get(
    "/teams/{team_id}/heroes",
    response_model=list[models.HeroPublic],
)
def read_team_heroes(
    team_id: int,
    session: SessionDep,
):
    team = session.get(models.Team, team_id)

    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found",
        )

    return team.heroes

@app.post("/missions", response_model=models.MissionPublic, status_code=201)
def create_mission(
    mission_in: models.MissionCreate,
    session: SessionDep,
):
    mission = models.Mission.model_validate(mission_in)

    session.add(mission)
    session.commit()
    session.refresh(mission)

    return mission

@app.post(
    "/heroes/{hero_id}/missions/{mission_id}",
    status_code=204,
)
def assign_hero_to_mission(
    hero_id: int,
    mission_id: int,
    session: SessionDep,
):
    hero = session.get(models.Hero, hero_id)

    if not hero:
        raise HTTPException(
            status_code=404,
            detail="Hero not found",
        )

    mission = session.get(models.Mission, mission_id)

    if not mission:
        raise HTTPException(
            status_code=404,
            detail="Mission not found",
        )

    if mission not in hero.missions:
        hero.missions.append(mission)
        session.add(hero)
        session.commit()

    return None


@app.get(
    "/heroes/{hero_id}/missions",
    response_model=list[models.MissionPublic],
)
def read_hero_missions(
    hero_id: int,
    session: SessionDep,
):
    hero = session.get(models.Hero, hero_id)

    if not hero:
        raise HTTPException(
            status_code=404,
            detail="Hero not found",
        )

    return hero.missions
