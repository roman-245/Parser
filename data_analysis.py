from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import Vacancy, Skill, Base
from config import DATABASE_URL

def analyze_data(session):
    # Получаем все навыки
    skills = session.query(Skill).all()

    # Создаем словарь для подсчета частоты каждого навыка
    skill_count = {skill.name: 0 for skill in skills}

    # Получаем все вакансии
    vacancies = session.query(Vacancy).all()

    # Суммируем частоту каждого навыка
    for vacancy in vacancies:
        for skill in vacancy.skills:
            skill_count[skill.name] += 1

    # Выводим навыки, которые встречаются в вакансиях с любой зарплатой
    print("Навыки, которые встречаются в вакансиях с любой зарплатой:")
    for skill, count in skill_count.items():
        if count > 0:
            print(f"{skill}: {count}")


if __name__ == "__main__":
    try:
        # Setup the database connection
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Perform data analysis
        analyze_data(session)
    except Exception as e:
        print(f"Error in data analysis: {e}")