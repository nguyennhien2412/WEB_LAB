from sqlmodel import Session, SQLModel, select

from app.database import engine
from app import models


def seed_database():
    # 1. Create tables if they do not exist
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # 2. Check whether database has already been seeded
        existing_team = session.exec(
            select(models.Team)
        ).first()

        if existing_team:
            print("Database already seeded. Nothing to do.")
            return

        # 3. Create missions
        battle_of_sokovia = models.Mission(
            title="Battle of Sokovia"
        )

        battle_of_new_york = models.Mission(
            title="Battle of New York"
        )

        # 4. Create teams
        avengers = models.Team(
            name="Avengers",
            headquarters="New York",
        )

        justice_league = models.Team(
            name="Justice League",
            headquarters="Metropolis",
        )

        # 5. Create heroes using relationships
        iron_man = models.Hero(
            name="Iron Man",
            age=35,
            secret_name="Tony Stark",
            team=avengers,
            missions=[battle_of_sokovia, battle_of_new_york],
        )

        captain_america = models.Hero(
            name="Captain America",
            age=100,
            secret_name="Steve Rogers",
            team=avengers,
            missions=[battle_of_sokovia],
        )

        thor = models.Hero(
            name="Thor",
            age=1500,
            secret_name="Thor Odinson",
            team=avengers,
            missions=[battle_of_sokovia],
        )

        hulk = models.Hero(
            name="Hulk",
            age=40,
            secret_name="Bruce Banner",
            team=avengers,
            missions=[battle_of_sokovia],
        )

        black_widow = models.Hero(
            name="Black Widow",
            age=35,
            secret_name="Natasha Romanoff",
            team=avengers,
            missions=[battle_of_new_york],
        )

        superman = models.Hero(
            name="Superman",
            age=35,
            secret_name="Clark Kent",
            team=justice_league,
            missions=[battle_of_new_york],
        )

        # 6. Add teams
        session.add(avengers)
        session.add(justice_league)

        # 7. Add heroes
        session.add(iron_man)
        session.add(captain_america)
        session.add(thor)
        session.add(hulk)
        session.add(black_widow)
        session.add(superman)

        # 8. Commit everything
        session.commit()

        print("Database seeded successfully.")


if __name__ == "__main__":
    seed_database()