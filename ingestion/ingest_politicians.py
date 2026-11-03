import json
import logging
import os
from pathlib import Path
from datetime import datetime
import sys

# Ensure the project root is in the path to allow imports
project_dir = Path(__file__).resolve().parents[1]
if str(project_dir) not in sys.path:
    sys.path.insert(0, str(project_dir))

from core.database import SessionLocal
from models.politicians import Politician

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_and_ingest(file_path=None):
    db = SessionLocal()
    configured_path = file_path or os.environ.get('LEGISLATORS_JSON_PATH')
    file_path = Path(configured_path) if configured_path else project_dir / 'data' / 'legislators-current.json'
    
    if not file_path.is_file():
        logger.error("Legislator source file not found at %s; set LEGISLATORS_JSON_PATH.", file_path)
        db.close()
        return 0
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        logger.info(f"Loaded {len(data)} records from JSON. Processing...")
        
        for item in data:
            # Extract necessary fields
            bioguide_id = item.get('id', {}).get('bioguide')
            if not bioguide_id:
                continue
                
            name_dict = item.get('name', {})
            first = name_dict.get('first', '')
            last = name_dict.get('last', '')
            full_name = f"{first} {last}".strip()
            
            bio = item.get('bio', {})
            dob_str = bio.get('birthday')
            dob = None
            if dob_str:
                try:
                    dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
                except ValueError:
                    pass
                    
            # Get the most recent term for chamber, party, state
            terms = item.get('terms', [])
            chamber = None
            party = None
            state_code = None
            district = None
            if terms:
                latest_term = terms[-1]
                chamber = latest_term.get('type')
                if chamber == 'rep':
                    chamber = 'House'
                elif chamber == 'sen':
                    chamber = 'Senate'
                party = latest_term.get('party')
                state_code = latest_term.get('state')
                district = str(latest_term.get('district', '')) if 'district' in latest_term else None

            # Upsert logic
            pol = db.query(Politician).filter(Politician.external_id == bioguide_id).first()
            if not pol:
                pol = Politician(
                    external_id=bioguide_id,
                    full_name=full_name,
                    chamber=chamber,
                    party=party,
                    state_code=state_code,
                    district=district,
                    date_of_birth=dob
                )
                db.add(pol)
            else:
                pol.full_name = full_name
                pol.chamber = chamber
                pol.party = party
                pol.state_code = state_code
                pol.district = district
                pol.date_of_birth = dob
                
        db.commit()
        logger.info("Successfully ingested politicians.")
        return len(data)
        
    except Exception:
        db.rollback()
        logger.exception("Error ingesting politicians")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    parse_and_ingest()
