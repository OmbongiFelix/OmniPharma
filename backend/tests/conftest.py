import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker, Session

from app.db.models import Base
from app.db.session import get_db
from app.main import app
from app.schemas.medication import MedicationContext
from app.schemas.patient import AllergyRecord, ConditionRecord, PatientContext

TEST_DATABASE_URL = "sqlite://"


# ---------------------------------------------------------------------------
# Single session-scoped engine + factory seeded once for all tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def engine():
    """Session-scoped in-memory SQLite engine with all tables created.

    Uses ``StaticPool`` so that all connections (from the test session and
    from FastAPI request handlers) share the same in-memory database.

    Returns:
        SQLAlchemy engine ready for use.
    """
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture(scope="session")
def session_factory(engine):
    """Session factory bound to the session-scoped engine.

    Args:
        engine: Session-scoped engine fixture.

    Returns:
        :class:`sessionmaker` instance.
    """
    return sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def _seed_once(engine, session_factory):
    """Seed the in-memory database once per test session.

    Imports seed logic directly so we don't rely on the file-based
    SessionLocal. Creates all ORM objects in a single session commit.

    Args:
        engine: Session-scoped engine.
        session_factory: Session factory.
    """
    _do_seed(session_factory)


def _do_seed(session_factory):
    """Populate all tables with demo data.

    Args:
        session_factory: Callable that returns a new session.
    """
    from app.db.models import (
        Allergy, AllergyCrossReactivity, Condition,
        ConditionDrugContraindication, InteractionRule, Inventory,
        Medication, MedicationHistory, Patient, PregnancyDrugWarning,
        Prescription,
    )

    db: Session = session_factory()
    try:
        if db.query(Patient).count() > 0:
            return  # Already seeded.

        # Medications
        meds_data = [
            ("metformin", "metformin", "Glucophage", "Tablet", "500 mg"),
            ("lisinopril", "lisinopril", "Zestril", "Tablet", "10 mg"),
            ("atorvastatin", "atorvastatin", "Lipitor", "Tablet", "20 mg"),
            ("warfarin", "warfarin", "Coumadin", "Tablet", "5 mg"),
            ("aspirin", "aspirin", "Aspirin", "Tablet", "75 mg"),
            ("amoxicillin", "amoxicillin", "Amoxil", "Capsule", "500 mg"),
            ("ibuprofen", "ibuprofen", "Brufen", "Tablet", "400 mg"),
            ("omeprazole", "omeprazole", "Prilosec", "Capsule", "20 mg"),
            ("salbutamol", "salbutamol", "Ventolin", "Inhaler", "100 mcg/dose"),
            ("prednisolone", "prednisolone", "Prednisolone", "Tablet", "5 mg"),
            ("amlodipine", "amlodipine", "Norvasc", "Tablet", "5 mg"),
            ("furosemide", "furosemide", "Lasix", "Tablet", "40 mg"),
            ("paracetamol", "paracetamol", "Panadol", "Tablet", "500 mg"),
            ("ciprofloxacin", "ciprofloxacin", "Ciprofloxacin", "Tablet", "500 mg"),
            ("doxycycline", "doxycycline", "Vibramycin", "Capsule", "100 mg"),
            ("glibenclamide", "glibenclamide", "Daonil", "Tablet", "5 mg"),
            ("metoprolol", "metoprolol", "Lopressor", "Tablet", "50 mg"),
            ("simvastatin", "simvastatin", "Zocor", "Tablet", "20 mg"),
            ("isotretinoin", "isotretinoin", "Roaccutane", "Capsule", "10 mg"),
            ("phenytoin", "phenytoin", "Dilantin", "Tablet", "100 mg"),
            ("sulfamethoxazole-trimethoprim", "sulfamethoxazole-trimethoprim", "Co-trimoxazole", "Tablet", "800/160 mg"),
            ("nitrofurantoin", "nitrofurantoin", "Nitrofurantoin", "Capsule", "100 mg"),
            ("diazepam", "diazepam", "Diazepam", "Tablet", "5 mg"),
            ("spironolactone", "spironolactone", "Spironolactone", "Tablet", "25 mg"),
        ]
        med_objects: dict[str, Medication] = {}
        for canonical, inn, trade, form, strength in meds_data:
            m = Medication(canonical_name=canonical, inn=inn, trade_name=trade,
                           dosage_form=form, strength=strength, source="synthetic demo")
            db.add(m)
            med_objects[canonical] = m
        db.flush()

        def mid(name: str) -> int:
            return med_objects[name].id

        # Patients
        patients_data = [
            ("OMNI-001", "Alice Kamau", "1985-03-15", "F", "PREGNANT", "NORMAL", "NORMAL", "NORMAL"),
            ("OMNI-002", "Brian Omondi", "1978-07-22", "M", "NOT_APPLICABLE", "NORMAL", "NORMAL", "NORMAL"),
            ("OMNI-003", "Cynthia Wanjiku", "1996-11-05", "F", "PREGNANT", "NORMAL", "NORMAL", "NORMAL"),
            ("OMNI-004", "David Mwangi", "1965-04-18", "M", "NOT_APPLICABLE", "NORMAL", "MODERATE_IMPAIRMENT", "NORMAL"),
            ("OMNI-005", "Esther Njeri", "1990-09-30", "F", "NOT_PREGNANT", "NORMAL", "NORMAL", "NORMAL"),
            ("OMNI-006", "Felix Ochieng", "1958-02-14", "M", "NOT_APPLICABLE", "MODERATE_IMPAIRMENT", "NORMAL", "UNKNOWN"),
            ("OMNI-007", "Grace Akinyi", "2002-06-25", "F", "NOT_PREGNANT", "NORMAL", "NORMAL", "NORMAL"),
            ("OMNI-008", "Hassan Ali", "1945-12-01", "M", "NOT_APPLICABLE", "MILD_IMPAIRMENT", "NORMAL", "NORMAL"),
            ("OMNI-009", "Irene Mukhwana", "1972-08-19", "F", "NOT_PREGNANT", "NORMAL", "NORMAL", "NORMAL"),
            ("OMNI-010", "John Kiptoo", "1980-01-10", "M", "NOT_APPLICABLE", "NORMAL", "NORMAL", "NORMAL"),
            ("OMNI-011", "Peter Mutiso", "1994-05-02", "M", "NOT_APPLICABLE", "NORMAL", "NORMAL", "DEFICIENT"),
            ("OMNI-012", "Mary Wambui", "1953-03-19", "F", "NOT_PREGNANT", "NORMAL", "NORMAL", "NORMAL"),
        ]
        patient_objects: list[Patient] = []
        for code, name, dob, sex, preg, renal, hepatic, g6pd in patients_data:
            p = Patient(patient_code=code, name=name, date_of_birth=dob, sex=sex,
                        pregnancy_status=preg, renal_status=renal,
                        hepatic_status=hepatic, g6pd_status=g6pd)
            db.add(p)
            patient_objects.append(p)
        db.flush()

        def pid(code: str) -> int:
            for p in patient_objects:
                if p.patient_code == code:
                    return p.id
            raise ValueError(f"Patient {code} not found")

        # Conditions
        for code, icd, name, status, onset in [
            ("OMNI-001", "Z34", "Normal pregnancy", "ACTIVE", "2026-01-15"),
            ("OMNI-003", "Z34", "Normal pregnancy", "ACTIVE", "2026-05-01"),
            ("OMNI-004", "K72", "Hepatic failure (chronic)", "ACTIVE", "2020-03-10"),
            ("OMNI-004", "E11", "Type 2 diabetes mellitus", "ACTIVE", "2015-06-20"),
            ("OMNI-005", "J45", "Asthma", "ACTIVE", "2008-04-12"),
            ("OMNI-006", "N18", "Chronic kidney disease stage 3", "ACTIVE", "2018-09-05"),
            ("OMNI-006", "E11", "Type 2 diabetes mellitus", "ACTIVE", "2016-11-20"),
            ("OMNI-007", "J06", "Upper respiratory tract infection", "ACTIVE", "2026-09-20"),
            ("OMNI-008", "I10", "Essential hypertension", "ACTIVE", "2000-01-01"),
            ("OMNI-009", "E11", "Type 2 diabetes mellitus", "ACTIVE", "2012-05-15"),
            ("OMNI-010", "I48", "Atrial fibrillation", "ACTIVE", "2019-03-22"),
            ("OMNI-011", "N39", "Urinary tract infection", "ACTIVE", "2026-09-20"),
            ("OMNI-012", "I10", "Hypertension", "ACTIVE", "2015-06-01"),
        ]:
            db.add(Condition(patient_id=pid(code), condition_code=icd,
                             condition_name=name, status=status, onset_date=onset))

        # Allergies
        for code, allergen, reaction, severity in [
            ("OMNI-001", "none", "none", "NONE"),
            ("OMNI-002", "none", "none", "NONE"),
            ("OMNI-003", "none", "none", "NONE"),
            ("OMNI-004", "none", "none", "NONE"),
            ("OMNI-005", "none", "none", "NONE"),
            ("OMNI-006", "none", "none", "NONE"),
            ("OMNI-007", "none", "none", "NONE"),
            ("OMNI-008", "sulfonamide", "Rash and urticaria", "MODERATE"),
            ("OMNI-009", "none", "none", "NONE"),
            ("OMNI-010", "penicillin", "Anaphylaxis", "SEVERE"),
            ("OMNI-011", "none", "none", "NONE"),
            ("OMNI-012", "none", "none", "NONE"),
        ]:
            db.add(Allergy(patient_id=pid(code), allergen=allergen,
                           reaction=reaction, severity=severity))

        # Prescriptions
        for code, med_name, dose, freq, route, start, end, status in [
            ("OMNI-001", "warfarin", "5 mg", "once daily", "oral", "2026-08-01", None, "ACTIVE"),
            ("OMNI-001", "aspirin", "75 mg", "once daily", "oral", "2026-08-01", None, "ACTIVE"),
            ("OMNI-002", "amlodipine", "5 mg", "once daily", "oral", "2026-07-01", None, "ACTIVE"),
            ("OMNI-003", "isotretinoin", "10 mg", "once daily", "oral", "2026-06-01", None, "ACTIVE"),
            ("OMNI-003", "lisinopril", "10 mg", "once daily", "oral", "2026-06-01", None, "ACTIVE"),
            ("OMNI-004", "atorvastatin", "20 mg", "once daily", "oral", "2021-01-01", None, "ACTIVE"),
            ("OMNI-004", "metformin", "500 mg", "twice daily", "oral", "2015-06-20", None, "ACTIVE"),
            ("OMNI-005", "salbutamol", "100 mcg", "as needed", "inhaled", "2008-04-12", None, "ACTIVE"),
            ("OMNI-005", "ibuprofen", "400 mg", "as needed", "oral", "2026-09-01", None, "ACTIVE"),
            ("OMNI-006", "metformin", "500 mg", "twice daily", "oral", "2016-11-20", None, "ACTIVE"),
            ("OMNI-006", "lisinopril", "10 mg", "once daily", "oral", "2026-08-15", None, "ACTIVE"),
            ("OMNI-007", "paracetamol", "500 mg", "four times daily", "oral", "2026-09-20", "2026-09-27", "ACTIVE"),
            ("OMNI-008", "amlodipine", "5 mg", "once daily", "oral", "2010-01-01", None, "ACTIVE"),
            ("OMNI-008", "metoprolol", "50 mg", "twice daily", "oral", "2010-01-01", None, "ACTIVE"),
            ("OMNI-009", "metformin", "500 mg", "twice daily", "oral", "2012-05-15", None, "ACTIVE"),
            ("OMNI-009", "glibenclamide", "5 mg", "once daily", "oral", "2015-06-01", None, "ACTIVE"),
            ("OMNI-010", "warfarin", "5 mg", "once daily", "oral", "2019-03-22", None, "ACTIVE"),
            ("OMNI-010", "amoxicillin", "500 mg", "three times daily", "oral", "2026-09-20", "2026-09-27", "ACTIVE"),
            ("OMNI-011", "sulfamethoxazole-trimethoprim", "800/160 mg", "twice daily", "oral", "2026-09-20", "2026-09-25", "ACTIVE"),
            ("OMNI-012", "diazepam", "5 mg", "at night", "oral", "2026-09-01", None, "ACTIVE"),
        ]:
            db.add(Prescription(patient_id=pid(code), medication_id=mid(med_name),
                                dose=dose, frequency=freq, route=route,
                                start_date=start, end_date=end, status=status))

        # Inventory
        for med_name, qty in {
            "metformin": 200, "lisinopril": 150, "atorvastatin": 120,
            "warfarin": 80, "aspirin": 300, "amoxicillin": 180,
            "ibuprofen": 250, "omeprazole": 200, "salbutamol": 60,
            "prednisolone": 100, "amlodipine": 140, "furosemide": 90,
            "paracetamol": 500, "ciprofloxacin": 120, "doxycycline": 100,
            "glibenclamide": 80, "metoprolol": 110, "simvastatin": 100,
            "isotretinoin": 40, "phenytoin": 60,
            "sulfamethoxazole-trimethoprim": 40, "nitrofurantoin": 35,
            "diazepam": 50, "spironolactone": 45,
        }.items():
            db.add(Inventory(medication_id=mid(med_name), quantity=qty,
                             facility="Demo Hospital Pharmacy", updated_at="2026-09-27T09:00:00"))

        # Interaction Rules
        for drug_a, drug_b, sev, mech, rec in [
            ("warfarin", "ibuprofen", "HIGH",
             "NSAIDs inhibit platelet aggregation and can displace warfarin from plasma proteins, raising INR and bleeding risk.",
             "Monitor INR closely; consider paracetamol for analgesia."),
            ("warfarin", "aspirin", "MODERATE",
             "Aspirin has antiplatelet activity; combined with warfarin the risk of bleeding is increased.",
             "Monitor INR; use lowest effective aspirin dose."),
            ("lisinopril", "spironolactone", "HIGH",
             "Dual renin-angiotensin-aldosterone blockade markedly increases hyperkalemia risk.",
             "Monitor serum potassium and creatinine frequently."),
            ("metformin", "furosemide", "LOW",
             "Loop diuretics may impair renal function and increase metformin accumulation risk.",
             "Monitor renal function regularly."),
        ]:
            db.add(InteractionRule(drug_a=drug_a, drug_b=drug_b, severity=sev,
                                   mechanism=mech, recommendation=rec,
                                   source="Demo rule", version="demo-1.0"))

        # Pregnancy warnings
        for drug, scope, sev, mech, rec in [
            ("isotretinoin", "ALL", "CONTRAINDICATED",
             "Isotretinoin is a known human teratogen.",
             "Absolutely contraindicated in pregnancy."),
            ("warfarin", "ALL", "HIGH",
             "Warfarin crosses the placenta; associated with fetal warfarin syndrome.",
             "Avoid; consider alternative anticoagulation."),
            ("lisinopril", "SECOND", "HIGH",
             "ACE inhibitors associated with fetopathy in second/third trimester.",
             "Avoid; switch to a pregnancy-appropriate antihypertensive."),
            ("ibuprofen", "THIRD", "HIGH",
             "NSAIDs in third trimester: premature ductus arteriosus closure risk.",
             "Avoid NSAIDs in third trimester."),
        ]:
            db.add(PregnancyDrugWarning(drug_name=drug, trimester_scope=scope,
                                        severity=sev, mechanism=mech, recommendation=rec,
                                        source="Demo rule", version="demo-1.0"))

        # Condition contraindications
        for cond, drug, ftype, sev, mech, rec in [
            ("RENAL-IMPAIRED", "metformin", "RENAL_CONTRAINDICATION", "HIGH",
             "Reduced renal clearance increases metformin accumulation and lactic acidosis risk.",
             "Avoid or dose-adjust per renal function."),
            ("RENAL-IMPAIRED", "ibuprofen", "RENAL_CONTRAINDICATION", "HIGH",
             "NSAIDs reduce renal perfusion and can worsen existing renal impairment.",
             "Avoid NSAIDs; use paracetamol."),
            ("HEPATIC-IMPAIRED", "atorvastatin", "HEPATIC_CONTRAINDICATION", "MODERATE",
             "Statins are hepatically metabolized; impairment raises hepatotoxicity risk.",
             "Use the lowest effective dose and monitor liver function."),
            ("HEPATIC-IMPAIRED", "paracetamol", "HEPATIC_CONTRAINDICATION", "MODERATE",
             "Reduced hepatic reserve lowers paracetamol safety margin.",
             "Reduce maximum daily dose and monitor."),
            ("N18", "lisinopril", "HYPERKALEMIA_RISK", "MODERATE",
             "ACE inhibition reduces potassium excretion; compounded by renal impairment.",
             "Check serum potassium before and after initiation."),
            ("N18", "spironolactone", "HYPERKALEMIA_RISK", "HIGH",
             "Potassium-sparing diuretics with reduced renal clearance markedly raise hyperkalemia risk.",
             "Avoid unless potassium is closely monitored."),
            ("G6PD-DEFICIENT", "sulfamethoxazole-trimethoprim", "G6PD_CONTRAINDICATION", "HIGH",
             "Sulfonamides are oxidative agents that can trigger acute hemolysis in G6PD deficiency.",
             "Avoid; select a non-oxidative antibiotic alternative."),
            ("G6PD-DEFICIENT", "nitrofurantoin", "G6PD_CONTRAINDICATION", "HIGH",
             "Nitrofurantoin is a recognized trigger of hemolysis in G6PD-deficient patients.",
             "Avoid; select a non-oxidative alternative."),
            ("J45", "ibuprofen", "RESPIRATORY_CONTRAINDICATION", "MODERATE",
             "NSAIDs can precipitate bronchospasm in NSAID-exacerbated respiratory disease.",
             "Avoid NSAIDs; use paracetamol."),
            ("J45", "aspirin", "RESPIRATORY_CONTRAINDICATION", "MODERATE",
             "Aspirin sensitivity is common in asthma; can cause severe bronchospasm.",
             "Avoid if any history of bronchospasm with these agents."),
        ]:
            db.add(ConditionDrugContraindication(condition_code=cond, drug_name=drug,
                                                  finding_type=ftype, severity=sev,
                                                  mechanism=mech, recommendation=rec,
                                                  source="Demo rule", version="demo-1.0"))

        # Allergy cross-reactivity
        for allergen, cross_drug, mech, sev in [
            ("penicillin", "amoxicillin",
             "Amoxicillin shares the beta-lactam ring structure responsible for penicillin allergy.",
             "HIGH"),
            ("penicillin", "ampicillin",
             "Ampicillin is an aminopenicillin sharing the beta-lactam structure.",
             "HIGH"),
            ("amoxicillin", "penicillin",
             "Amoxicillin and penicillin share the beta-lactam ring structure.",
             "MODERATE"),
            ("sulfonamide", "sulfamethoxazole-trimethoprim",
             "Co-trimoxazole contains sulfamethoxazole; cross-reactive with sulfonamide allergy.",
             "HIGH"),
        ]:
            db.add(AllergyCrossReactivity(allergen=allergen, cross_reactive_drug=cross_drug,
                                          mechanism=mech, severity=sev,
                                          source="Demo rule", version="demo-1.0"))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Per-test DB session
# ---------------------------------------------------------------------------

@pytest.fixture()
def db(session_factory):
    """Per-test database session (rolled back after each test).

    Args:
        session_factory: Session factory fixture.

    Yields:
        Active SQLAlchemy session.
    """
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ---------------------------------------------------------------------------
# FastAPI TestClient wired to the test DB
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client(engine, session_factory, _seed_once):
    """Session-scoped FastAPI TestClient with the test DB injected.

    The ``TestClient`` is created with ``raise_server_exceptions=True``
    and the ``get_db`` dependency is overridden so every request handler
    receives a session bound to the in-memory test engine instead of the
    on-disk production engine.  The app lifespan is suppressed so that
    ``create_all_tables()`` does not run on the production engine during
    tests (tables are already created by the ``engine`` fixture above).

    Args:
        engine: Session-scoped test engine.
        session_factory: Session factory.
        _seed_once: Ensures seeding is complete before client is used.

    Yields:
        :class:`fastapi.testclient.TestClient` ready for requests.
    """
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    # Set raise_server_exceptions=False so 500 errors surface as HTTP responses.
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Factory helpers for rule unit tests
# ---------------------------------------------------------------------------

def make_med(canonical_name: str, **kwargs) -> MedicationContext:
    """Create a minimal MedicationContext for unit tests.

    Args:
        canonical_name: The canonical drug name.
        **kwargs: Optional overrides for any MedicationContext field.

    Returns:
        A :class:`~app.schemas.medication.MedicationContext` instance.
    """
    return MedicationContext(canonical_name=canonical_name, **kwargs)


def make_patient(**kwargs) -> PatientContext:
    """Create a minimal PatientContext for unit tests.

    Provides sensible defaults for all required fields; override as needed.

    Args:
        **kwargs: Field overrides for PatientContext.

    Returns:
        A :class:`~app.schemas.patient.PatientContext` instance.
    """
    defaults = dict(
        id=1,
        patient_code="TEST-001",
        name="Test Patient",
        date_of_birth="1985-01-01",
        sex="F",
        pregnancy_status="NOT_PREGNANT",
        renal_status="NORMAL",
        hepatic_status="NORMAL",
        g6pd_status="NORMAL",
        allergies=[],
        conditions=[],
        current_prescriptions=[],
        medication_history=[],
    )
    defaults.update(kwargs)
    return PatientContext(**defaults)
