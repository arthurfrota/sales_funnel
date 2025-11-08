from __future__ import annotations

from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import Company, Workspace


def ensure_bootstrap_data() -> None:
    with SessionLocal() as session:  # type: Session
        company = session.query(Company).filter(Company.name == "Default Company").first()
        if not company:
            company = Company(name="Default Company", sector="generic", country="BR")
            session.add(company)
            session.commit()
            session.refresh(company)
        workspace = (
            session.query(Workspace)
            .filter(Workspace.company_id == company.id, Workspace.name == "Default Workspace")
            .first()
        )
        if not workspace:
            workspace = Workspace(company_id=company.id, name="Default Workspace")
            session.add(workspace)
            session.commit()
