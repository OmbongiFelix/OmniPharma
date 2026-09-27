import sys
sys.stdout.reconfigure(encoding="utf-8")
import httpx
from bs4 import BeautifulSoup

resp = httpx.get(
    "https://products.pharmacyboardkenya.org/ppb_admin/pages/public_view_retention_products.php",
    timeout=20,
    follow_redirects=True,
)
soup = BeautifulSoup(resp.text, "html.parser")

# Tables
tables = soup.find_all("table")
print(f"Tables found: {len(tables)}")
for i, t in enumerate(tables):
    headers = [th.get_text(strip=True) for th in t.find_all("th")]
    rows = t.find_all("tr")
    print(f"  Table {i}: {len(rows)} rows, headers={headers}")
    if rows:
        first_data_row = rows[1] if len(rows) > 1 else rows[0]
        cells = [td.get_text(strip=True)[:60] for td in first_data_row.find_all("td")]
        print(f"  First data row sample: {cells}")

# Forms
forms = soup.find_all("form")
print(f"\nForms: {len(forms)}")
for f in forms:
    print(f"  action={f.get('action')}, method={f.get('method')}")
    for inp in f.find_all(["input", "select"]):
        print(f"    {inp.name} name={inp.get('name')} type={inp.get('type')} value={inp.get('value')}")

# Pagination links
print("\n--- Pagination hints ---")
for a in soup.find_all("a"):
    href = a.get("href", "")
    text = a.get_text(strip=True)
    if any(x in text.lower() for x in ["next", "prev", "page"]) or "page" in href.lower():
        print(f"  link: {text!r} -> {href}")

# Scripts
scripts_text = " ".join(s.get_text() for s in soup.find_all("script"))
print(f"\nDataTables present: {'DataTable' in scripts_text or 'dataTables' in scripts_text}")
print(f"AJAX calls: {'ajax' in scripts_text.lower()}")
print(f"draw/sEcho: {'sEcho' in scripts_text or 'draw' in scripts_text}")

# Full HTML tail
print("\n--- HTML tail (last 3000 chars) ---")
print(resp.text[-3000:])
