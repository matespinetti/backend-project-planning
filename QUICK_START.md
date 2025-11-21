# Quick Start: Real Bonita Test Data

## TL;DR - 3 Steps to Real Bonita Data

### 1️⃣ Create Test Data
```bash
uv run python create_bonita_test_data.py
```

**What happens:**
- Creates pending project with real Bonita process
- Saves data to `test_project_data.json`
- Shows all project and Bonita IDs

**Output includes:**
- `project_id` (UUID)
- `bonita_case_id` (real from Bonita)
- `bonita_process_instance_id` (real from Bonita)
- 2 etapas with 5 PENDIENTE pedidos

---

### 2️⃣ Test Offer Acceptance
```bash
uv run python test_offer_acceptance.py
```

**What happens:**
- Loads test project data
- Creates offers on PENDIENTE pedidos
- Tests accepting one offer
- Shows updated project state

**Key results:**
- Offers created successfully
- Offer acceptance tested
- Project state transitions verified

---

### 3️⃣ Monitor in Bonita Portal
```
http://localhost:8080/bonita/portal/

Login: BONITA_USERNAME / BONITA_PASSWORD

Navigate to: Case {bonita_case_id}
```

**What you see:**
- Process instance execution
- Process variables
- State transitions
- Audit trail

---

## The Problem This Solves

**Before:**
```python
# Hardcoded fake Bonita data
bonita_case_id="CASE-2024-002"  # ❌ Fake
bonita_process_instance_id=1002  # ❌ Fake

# Cannot test real offer workflows ❌
```

**After:**
```python
# Real Bonita data from actual process
bonita_case_id="12345"  # ✅ Real
bonita_process_instance_id=67890  # ✅ Real

# Can test complete offer workflows ✅
```

---

## Prerequisites (5-Minute Check)

All three services must be running:

### 1. Proxy API (this service)
```bash
# Terminal 1
uv run uvicorn app.main:app --reload
# Visit: http://localhost:8000/health
```

### 2. Cloud API
```
# Should be running on URL from .env: CLOUD_API_URL
curl {CLOUD_API_URL}/health
# Should return 200 OK
```

### 3. Bonita BPM
```
# Should be running on URL from .env: BONITA_URL
http://localhost:8080/bonita/
# Should show Bonita login page
```

---

## What Gets Created

### Project Structure
```
Centro Comunitario Testeable
├── Estado: en_planificacion (PENDIENTE financing)
├── Bonita Case: 12345 (REAL)
│
├── Etapa 1: Fundaciones y Estructura (90 days)
│   ├── Pedido 1: ECONOMICO - 180,000 ARS ← PENDIENTE (offer here!)
│   ├── Pedido 2: MANO_OBRA - 6 workers ← PENDIENTE (offer here!)
│   └── Pedido 3: EQUIPAMIENTO - 1 set ← PENDIENTE (offer here!)
│
└── Etapa 2: Construcción de Paredes y Techo (90 days)
    ├── Pedido 1: MATERIALES - 20,000 ladrillos ← PENDIENTE (offer here!)
    └── Pedido 2: ECONOMICO - 45,000 ARS ← PENDIENTE (offer here!)
```

**5 PENDIENTE pedidos ready for offers!**

---

## Test Data Output Example

```json
{
  "proyecto": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "titulo": "Centro Comunitario Testeable",
    "estado": "en_planificacion",
    "bonita_case_id": "12345",
    "bonita_process_instance_id": 67890,
    "etapas": [
      {
        "id": "uuid-etapa-1",
        "nombre": "Fundaciones y Estructura",
        "pedidos": [
          {
            "id": "uuid-pedido-1",
            "tipo": "economico",
            "estado": "PENDIENTE",
            "monto": 180000.0
          }
        ]
      }
    ]
  },
  "bonita_case_id": "12345",
  "bonita_process_url": "http://localhost:8080/bonita/portal/resource/processInstance/12345/content/"
}
```

---

## Common Tasks

### Create an Offer
```bash
# Get pedido_id from test_project_data.json

curl -X POST http://localhost:8000/api/v1/ofertas \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {TOKEN}" \
  -d '{
    "pedido_id": "uuid-from-test-data",
    "monto_ofrecido": 170000.0,
    "descripcion": "Materiales de calidad con entrega rápida"
  }'
```

### Accept an Offer
```bash
curl -X PATCH http://localhost:8000/api/v1/ofertas/{oferta_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {TOKEN}" \
  -d '{
    "estado": "aceptada"
  }'
```

### Check Pedido Status
```bash
curl -X GET "http://localhost:8000/api/v1/pedidos/{pedido_id}" \
  -H "Authorization: Bearer {TOKEN}"
```

### View Bonita Process
```
1. Open: http://localhost:8080/bonita/portal/
2. Login with BONITA_USERNAME / BONITA_PASSWORD
3. Find case with ID: {bonita_case_id}
4. Click to see process execution
```

---

## Troubleshooting (2-Minute Fix)

| Problem | Fix |
|---------|-----|
| **"Connection refused"** | Proxy API not running? `uv run uvicorn app.main:app --reload` |
| **"Cloud API unreachable"** | Check CLOUD_API_URL in .env |
| **"Bonita process failed"** | Check BONITA_URL and credentials in .env |
| **"test_project_data.json not found"** | Run `create_bonita_test_data.py` first |
| **"User already exists"** | Normal! Script uses login instead |
| **"404 Not Found"** | Check API URL prefix: should be `/api/v1/` |

---

## Files Created

| File | Purpose |
|------|---------|
| `create_bonita_test_data.py` | Create test data with real Bonita |
| `test_offer_acceptance.py` | Test offer workflows |
| `test_project_data.json` | Generated project data (auto-created) |
| `BONITA_TEST_DATA_GUIDE.md` | Full documentation (30 min read) |
| `IMPLEMENTATION_SUMMARY.md` | Technical details (20 min read) |
| `QUICK_START.md` | This file (5 min read) |

---

## Success Checklist

After running both scripts:

- [ ] ✅ `create_bonita_test_data.py` completed successfully
- [ ] ✅ `test_project_data.json` was created
- [ ] ✅ Real `bonita_case_id` displayed (e.g., "12345", not "CASE-2024-002")
- [ ] ✅ `test_offer_acceptance.py` completed successfully
- [ ] ✅ Multiple offers were created
- [ ] ✅ At least one offer was accepted
- [ ] ✅ Project state changed in response
- [ ] ✅ Can see case in Bonita portal

If all checked: **You're ready to test real workflows!** 🎉

---

## Next: What Can You Test?

With real Bonita data, you can now:

✅ Create multiple offers per pedido
✅ Test offer acceptance workflows
✅ Monitor Bonita process execution
✅ Track pedido state transitions
✅ Test etapa financing workflows
✅ Verify project state changes
✅ Run end-to-end integration tests

---

## Need More Details?

- **Full guide:** Read `BONITA_TEST_DATA_GUIDE.md`
- **Technical details:** Read `IMPLEMENTATION_SUMMARY.md`
- **Architecture:** Read `CLAUDE.md`
- **API reference:** Visit http://localhost:8000/docs

---

## One-Liner Quick Test

```bash
# Create test data AND test offers in one go
uv run python create_bonita_test_data.py && sleep 2 && uv run python test_offer_acceptance.py
```

Done! You now have real Bonita processes for testing. 🚀
