from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.models.skill import Interest, Skill, UserInterest, UserSkill
from app.models.user import User


def _normalized(value: str) -> tuple[str, str]:
    name = " ".join(value.strip().split())
    return name, name.casefold()


class SkillService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def set_skills(self, user: User, names: list[str]) -> list[Skill]:
        result = []
        seen: set[str] = set()
        for raw in names:
            name, normalized = _normalized(raw)
            if normalized in seen:
                continue
            seen.add(normalized)
            skill = self.db.scalar(select(Skill).where(Skill.normalized_name == normalized))
            if skill is None:
                skill = Skill(name=name, normalized_name=normalized)
                try:
                    with self.db.begin_nested():
                        self.db.add(skill)
                        self.db.flush()
                except IntegrityError:
                    skill = self.db.scalar(select(Skill).where(Skill.normalized_name == normalized))
            if skill is None:
                raise ConflictError("Could not create skill.")
            exists = self.db.scalar(select(UserSkill).where(UserSkill.user_id == user.id, UserSkill.skill_id == skill.id))
            if exists is None:
                self.db.add(UserSkill(user_id=user.id, skill_id=skill.id))
            result.append(skill)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Skill association already exists.") from None
        return result

    def remove_skill(self, user: User, skill_id):
        link = self.db.scalar(select(UserSkill).where(UserSkill.user_id == user.id, UserSkill.skill_id == skill_id))
        if link is not None:
            self.db.delete(link)
            self.db.commit()

    def set_interests(self, user: User, names: list[str]) -> list[Interest]:
        result = []
        seen: set[str] = set()
        for raw in names:
            name, normalized = _normalized(raw)
            if normalized in seen:
                continue
            seen.add(normalized)
            interest = self.db.scalar(select(Interest).where(Interest.normalized_name == normalized))
            if interest is None:
                interest = Interest(name=name, normalized_name=normalized)
                try:
                    with self.db.begin_nested():
                        self.db.add(interest)
                        self.db.flush()
                except IntegrityError:
                    interest = self.db.scalar(select(Interest).where(Interest.normalized_name == normalized))
            if interest is None:
                raise ConflictError("Could not create interest.")
            exists = self.db.scalar(select(UserInterest).where(UserInterest.user_id == user.id, UserInterest.interest_id == interest.id))
            if exists is None:
                self.db.add(UserInterest(user_id=user.id, interest_id=interest.id))
            result.append(interest)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ConflictError("Interest association already exists.") from None
        return result

    def remove_interest(self, user: User, interest_id):
        link = self.db.scalar(select(UserInterest).where(UserInterest.user_id == user.id, UserInterest.interest_id == interest_id))
        if link is not None:
            self.db.delete(link)
            self.db.commit()
