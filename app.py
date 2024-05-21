import requests
from bs4 import BeautifulSoup
import fake_useragent
import time
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from config import DATABASE_URL
from datetime import datetime
from logging_config import logger

# Define the ORM base
Base = declarative_base()

# Define the Vacancy model
class Vacancy(Base):
    __tablename__ = 'vacancies'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    salary = Column(String)
    text = Column(String)
    created = Column(DateTime, default=datetime.now)
    skills = relationship("Skill", secondary="connection_table")

# Define the Skill model
class Skill(Base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True)
    name = Column(String)

# Define the ConnectionTable model
class ConnectionTable(Base):
    __tablename__ = 'connection_table'
    vacancy_id = Column(Integer, ForeignKey('vacancies.id'), primary_key=True)
    skill_id = Column(Integer, ForeignKey('skills.id'), primary_key=True)
def get_page_count():
    ua = fake_useragent.UserAgent()
    res = requests.get(
        url="https://hh.ru/stazhirovki",
        headers={"user-agent": ua.random}
    )
    if res.status_code != 200:
        print(f"Failed to fetch initial page: {res.status_code}")
        return 0
    soup = BeautifulSoup(res.content, "lxml")
    try:
        # Extract the total number of pages from the pagination block
        page_count = int(soup.find("div", {"data-qa": "pager-block"}).find_all("a", {"data-qa": "pager-page"})[-1].text)
        return page_count
    except Exception as e:
        print(f"Error extracting page count: {e}")
        return 0
def get_links(page_count):
    ua = fake_useragent.UserAgent()
    links = []
    for page in range(page_count):
        try:
            res = requests.get(url=f"https://hh.ru/stazhirovki?page={page}", headers={"user-agent": ua.random})
            res.raise_for_status()
            res.encoding = res.apparent_encoding  # Обработать кодировку
            soup = BeautifulSoup(res.content, "lxml")
            page_links = soup.find_all("a", {"class": "bloko-link"}, href=True)
            for a in page_links:
                href = a.get("href")
                if href.startswith("https://hh.ru/vacancy"):
                    links.append(href)
                    logger.info(f"Found link: {href}")
        except Exception as e:
            logger.error(f"Error on page {page}: {e}")
        time.sleep(1)
    return links

def get_resume(link):
    ua = fake_useragent.UserAgent()
    try:
        response = requests.get(url=link, headers={"user-agent": ua.random})
        response.raise_for_status()
        response.encoding = response.apparent_encoding  # Обработать кодировку
        soup = BeautifulSoup(response.content, "lxml")
        name = soup.find(attrs={"data-qa": "vacancy-title"}).text.strip() if soup.find(attrs={"data-qa": "vacancy-title"}) else ""
        salary = soup.find(attrs={"data-qa": "vacancy-salary-compensation-type-net"}).text.replace("\u2009", "").replace("\xa0", " ") if soup.find(attrs={"data-qa": "vacancy-salary-compensation-type-net"}) else ""
        text = soup.find("div", {"data-qa": "vacancy-description"}).text.strip() if soup.find("div", {"data-qa": "vacancy-description"}) else ""
        skills = [tag.text.strip() for tag in soup.find_all("span", {"class": "bloko-tag__section_text"})]
        return {"name": name, "salary": salary, "text": text, "skills": skills}
    except Exception as e:
        logger.error(f"Failed to fetch link {link}: {e}")
        return None

def download_data(session):
    page_count = get_page_count()
    logger.info(f"Found {page_count} pages")
    links = get_links(page_count)
    logger.info(f"Found {len(links)} links")
    for link in links:
        resume = get_resume(link)
        if resume:
            vacancy = Vacancy(name=resume['name'], salary=resume['salary'], text=resume['text'])
            for skill_name in resume['skills']:
                skill = session.query(Skill).filter_by(name=skill_name).first()
                if not skill:
                    skill = Skill(name=skill_name)
                    session.add(skill)
                vacancy.skills.append(skill)
            session.add(vacancy)
            session.commit()  # Сохраняем данные после добавления вакансии
            logger.info(f"Added vacancy: {resume['name']}")  # Логируем добавленную вакансию
            time.sleep(1)
    logger.info("All data saved to database")

if __name__ == "__main__":
    try:
        # Setup the database
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # Download data and save to database
        download_data(session)
    except Exception as e:
        logger.error(f"Error in main execution: {e}")