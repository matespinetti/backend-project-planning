# Real Bonita Testing - Complete Documentation

## Overview

This directory now contains **complete tools and documentation** for creating and testing projects with **real Bonita process instances** instead of hardcoded fake data.

## The Problem We Solved

Previously, test data had hardcoded fake Bonita IDs:
```python
bonita_case_id="CASE-2024-002"           # ❌ Fake
bonita_process_instance_id=1002          # ❌ Fake
# Cannot test real offer acceptance workflows
```

Now you have **real Bonita processes** for testing:
```python
bonita_case_id="12345"                   # ✅ Real from Bonita
bonita_process_instance_id=67890         # ✅ Real from Bonita
# Can test complete offer acceptance workflows!
```

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites Checklist
- [ ] Proxy API running: `http://localhost:8000/health`
- [ ] Cloud API accessible: `{CLOUD_API_URL}/health`
- [ ] Bonita running: `http://localhost:8080/bonita/`

### 1. Create Test Data
```bash
uv run python create_bonita_test_data.py
```

**Output:** Project with real `bonita_case_id` and saved to `test_project_data.json`

### 2. Test Offer Acceptance
```bash
uv run python test_offer_acceptance.py
```

**Output:** Offers created and accepted, state changes shown

### 3. Monitor in Bonita
```
http://localhost:8080/bonita/portal/
→ Find case by case_id from step 1
```

**Done!** You now have real Bonita processes for testing. 🎉

---

## 📚 Documentation Guide

Choose based on your needs:

### For the Impatient (5 min read)
→ **[QUICK_START.md](./QUICK_START.md)**
- 3-step quickstart
- Common tasks
- Quick troubleshooting

### For Complete Information (30 min read)
→ **[BONITA_TEST_DATA_GUIDE.md](./BONITA_TEST_DATA_GUIDE.md)**
- Architecture overview
- Prerequisites
- Step-by-step guide
- Customization
- Comprehensive troubleshooting
- Best practices

### For Technical Details (20 min read)
→ **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)**
- What was created
- Architecture changes
- Implementation details
- File references
- Success indicators

### For File Overview (5 min read)
→ **[FILES_CREATED.txt](./FILES_CREATED.txt)**
- Summary of all files
- File purposes
- Quick reference matrix
- Directory structure

### For Project Architecture (Read CLAUDE.md)
→ **[CLAUDE.md](./CLAUDE.md)**
- Full project architecture
- Microservices design
- Data flow diagrams
- API contracts
- Configuration

---

## 🔧 Executable Scripts

### `create_bonita_test_data.py`
**Creates realistic pending projects with real Bonita processes**

```bash
uv run python create_bonita_test_data.py
```

**What it does:**
- Registers test user (or uses existing)
- Creates pending project with real Bonita process
- 2 etapas with 5 PENDIENTE pedidos total
- Saves response to `test_project_data.json`
- Displays all IDs and project structure

**Output:**
```
✅ PROJECT CREATED SUCCESSFULLY WITH REAL BONITA INTEGRATION!

📋 PROJECT DETAILS:
   ID:              a1b2c3d4-e5f6...
   Título:          Centro Comunitario Testeable
   ...
🔄 BONITA BPM INTEGRATION:
   Case ID:         12345              ← REAL!
   Process Instance: 67890             ← REAL!
```

### `test_offer_acceptance.py`
**Tests offer creation and acceptance workflows**

```bash
uv run python test_offer_acceptance.py
```

**What it does:**
- Loads test project from `test_project_data.json`
- Authenticates as test user
- Creates offers on all PENDIENTE pedidos
- Tests accepting one offer
- Shows updated project state

**Output:**
```
📊 PEDIDOS SUMMARY (Available for Offers)
🎯 CREATING OFFERS ON PENDIENTE PEDIDOS
💬 TESTING OFFER ACCEPTANCE
✅ OFFER ACCEPTANCE TEST COMPLETED
```

---

## 📁 Files Created

| File | Type | Purpose |
|------|------|---------|
| `create_bonita_test_data.py` | Script | Create test projects with real Bonita |
| `test_offer_acceptance.py` | Script | Test offer workflows |
| `QUICK_START.md` | Doc | 5-minute overview |
| `BONITA_TEST_DATA_GUIDE.md` | Doc | Complete 30-minute guide |
| `IMPLEMENTATION_SUMMARY.md` | Doc | Technical details |
| `FILES_CREATED.txt` | Doc | File reference |
| `README_BONITA_TESTING.md` | Doc | This file |
| `test_project_data.json` | Generated | Project data with real IDs |

---

## 🎯 What You Can Test

With real Bonita data, you can now test:

✅ **Offer Creation**
- Create multiple offers per pedido
- Different offer amounts
- Different descriptions

✅ **Offer Acceptance**
- Accept offers
- Reject offers
- Track state changes

✅ **State Transitions**
- Pedido: PENDIENTE → COMPROMETIDO → COMPLETADO
- Etapa: PENDIENTE → FINANCIADA → EN_EJECUCION
- Proyecto: PENDIENTE → EN_EJECUCION → FINALIZADO

✅ **Bonita Integration**
- Monitor process execution
- View case variables
- Track audit trail
- Test human tasks

✅ **End-to-End Workflows**
- Full project lifecycle testing
- Integration testing
- Performance testing

---

## 🔍 Understanding the Architecture

### Data Flow: Create Project with Real Bonita

```
Your Script
    ↓
POST /api/v1/projects
    ↓
Proxy API (Orchestrator)
    ├─→ Cloud API: Create proyecto, etapas, pedidos
    │   Response: Real UUID from database
    ├─→ Bonita BPM: Start process with UUID
    │   Response: Real case_id, process_instance_id
    └─→ Cloud API: Update with Bonita info
    ↓
Response with REAL bonita_case_id + process_instance_id
    ↓
Your Script
    ↓
Save to test_project_data.json
```

### Why This Matters

| Aspect | Before | After |
|--------|--------|-------|
| **Bonita Data** | Hardcoded fake | Real from Bonita ✨ |
| **Can test offers?** | ❌ No | ✅ Yes |
| **Can test workflows?** | ❌ No | ✅ Yes |
| **Can monitor Bonita?** | ❌ No | ✅ Yes |
| **Useful for testing** | Limited | Complete |

---

## 📊 Data Created by Scripts

### Project Structure
```
Centro Comunitario Testeable
├── Estado: en_planificacion (waiting for financing)
├── Bonita Case: 12345 (REAL)
│
├── Etapa 1: Fundaciones y Estructura
│   ├── Pedido 1: ECONOMICO - 180,000 ARS [PENDIENTE] ← Offer here!
│   ├── Pedido 2: MANO_OBRA - 6 workers [PENDIENTE] ← Offer here!
│   └── Pedido 3: EQUIPAMIENTO - 1 set [PENDIENTE] ← Offer here!
│
└── Etapa 2: Construcción de Paredes y Techo
    ├── Pedido 1: MATERIALES - 20,000 ladrillos [PENDIENTE] ← Offer here!
    └── Pedido 2: ECONOMICO - 45,000 ARS [PENDIENTE] ← Offer here!
```

**5 PENDIENTE pedidos ready for offer testing!**

---

## 🐛 Troubleshooting

### Quick Fixes

| Problem | Fix |
|---------|-----|
| **"Connection refused"** | Start Proxy API: `uv run uvicorn app.main:app --reload` |
| **"Cloud API unreachable"** | Check CLOUD_API_URL in .env |
| **"Bonita failed"** | Check BONITA_URL, username, password in .env |
| **"test_project_data.json not found"** | Run `create_bonita_test_data.py` first |
| **"User already exists"** | Normal! Script continues with login |

### Detailed Troubleshooting

See: **[BONITA_TEST_DATA_GUIDE.md](./BONITA_TEST_DATA_GUIDE.md#troubleshooting-guide)**

---

## 💡 Common Tasks

### Create an Offer
```bash
curl -X POST http://localhost:8000/api/v1/ofertas \
  -H "Authorization: Bearer {TOKEN}" \
  -d '{
    "pedido_id": "{pedido_id}",
    "monto_ofrecido": 170000.0,
    "descripcion": "Oferta competitiva"
  }'
```

### Accept an Offer
```bash
curl -X PATCH http://localhost:8000/api/v1/ofertas/{oferta_id} \
  -H "Authorization: Bearer {TOKEN}" \
  -d '{"estado": "aceptada"}'
```

### View Project
```bash
curl -X GET http://localhost:8000/api/v1/projects/{project_id} \
  -H "Authorization: Bearer {TOKEN}"
```

### Monitor in Bonita
```
http://localhost:8080/bonita/portal/
Login → Find case {bonita_case_id} → View process
```

---

## 🎓 Learning Path

### Day 1: Get Started (30 minutes)
1. Read: **QUICK_START.md**
2. Run: `create_bonita_test_data.py`
3. Run: `test_offer_acceptance.py`
4. Visit: Bonita portal with case_id

### Day 2: Understand Details (1 hour)
1. Read: **BONITA_TEST_DATA_GUIDE.md**
2. Customize: Modify project creation in script
3. Test: Create scenarios for your needs

### Day 3: Deep Dive (2-3 hours)
1. Read: **IMPLEMENTATION_SUMMARY.md**
2. Read: **CLAUDE.md** (architecture)
3. Explore: API endpoints in `/docs`
4. Integrate: Test data with your test suite

### Beyond: Production Testing
1. Create scenario-specific scripts
2. Integrate with CI/CD pipeline
3. Automate workflow testing
4. Monitor performance

---

## 📖 Complete File Index

### Scripts
- `create_bonita_test_data.py` - Create test data
- `test_offer_acceptance.py` - Test offers

### Documentation (Start Here)
- `README_BONITA_TESTING.md` - This file
- `QUICK_START.md` - 5-minute start
- `BONITA_TEST_DATA_GUIDE.md` - 30-minute guide
- `IMPLEMENTATION_SUMMARY.md` - Technical details
- `FILES_CREATED.txt` - File reference

### Generated
- `test_project_data.json` - Created by script

### Architecture & API
- `CLAUDE.md` - Project architecture
- `CLOUD_API_DOCUMENTATION.md` - Cloud API endpoints
- `PROXY_API_DOCUMENTATION.md` - Proxy API endpoints

---

## ✅ Success Checklist

After completing quick start:

- [ ] Read QUICK_START.md
- [ ] Run create_bonita_test_data.py successfully
- [ ] See real bonita_case_id in output (not "CASE-2024-XXX")
- [ ] test_project_data.json was created
- [ ] Run test_offer_acceptance.py successfully
- [ ] See multiple offers created
- [ ] See offer acceptance work
- [ ] Access Bonita portal with case_id
- [ ] See real process in Bonita

**All checked? You're ready for testing! 🎉**

---

## 🤝 Support

**For quick questions:**
- See QUICK_START.md

**For detailed guidance:**
- See BONITA_TEST_DATA_GUIDE.md

**For technical issues:**
- See IMPLEMENTATION_SUMMARY.md troubleshooting

**For architecture questions:**
- See CLAUDE.md

**For API reference:**
- Visit http://localhost:8000/docs (Swagger UI)

---

## 🔄 Workflow Summary

### One-Time Setup
```bash
# Create test data with real Bonita
uv run python create_bonita_test_data.py
# Output: test_project_data.json with real IDs
```

### Testing Offers
```bash
# Test offer workflows
uv run python test_offer_acceptance.py
# Automatically loads test_project_data.json
```

### Monitoring
```
# View Bonita process
http://localhost:8080/bonita/portal/
# Find case by case_id from test_project_data.json
```

---

## 🎯 Key Takeaways

1. **Real Bonita Data** - No more fake hardcoded IDs
2. **Easy to Use** - Two simple scripts
3. **Well Documented** - Multiple documentation levels
4. **Flexible** - Easy to customize
5. **Complete** - Everything needed for testing

---

## 📞 Questions?

1. Check **QUICK_START.md** for basics
2. Check **BONITA_TEST_DATA_GUIDE.md** for details
3. Check **IMPLEMENTATION_SUMMARY.md** for technical info
4. Check script help: `python create_bonita_test_data.py --help`

---

## 🚀 Next Steps

**Right now:**
```bash
uv run python create_bonita_test_data.py
uv run python test_offer_acceptance.py
```

**After that:**
- Read the detailed guide
- Customize for your needs
- Integrate with your tests
- Monitor in Bonita

---

**Version:** 1.0
**Created:** 2025-01-15
**Status:** Ready for production testing

Start with: **QUICK_START.md** ← Click here to get started!

---

## 📚 Documentation Map

```
README_BONITA_TESTING.md (YOU ARE HERE)
    ├─ Quick Start (5 min) → QUICK_START.md
    ├─ Full Guide (30 min) → BONITA_TEST_DATA_GUIDE.md
    ├─ Technical (20 min) → IMPLEMENTATION_SUMMARY.md
    ├─ File Reference → FILES_CREATED.txt
    ├─ Architecture → CLAUDE.md
    ├─ API Endpoints → /docs (interactive)
    └─ Bonita Help → Portal help

Scripts to Run:
    ├─ Create Data → create_bonita_test_data.py
    └─ Test Offers → test_offer_acceptance.py
```

---

**Ready?** Start with [QUICK_START.md](./QUICK_START.md) 🚀
