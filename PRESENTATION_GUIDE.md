# SyncScript 7-Minute Presentation Guide

## Timing Breakdown

| Section | Time | Rubric Category |
|---------|------|-----------------|
| Hook + Problem | 0:30 | — |
| Architecture Overview | 1:00 | Architecture (25%) |
| Live Demo: Core Flow | 2:30 | Real-Time (25%) + UX (15%) |
| Security Deep-Dive | 1:00 | Security (20%) |
| Edge Features | 1:00 | Creativity (15%) |
| Closing + Scale Story | 1:00 | — |

---

## 0:00-0:30 — The Hook (30 sec)

**Open strong with the problem:**

> "Researchers lose 30% of their time hunting for sources they've already found. Google Docs can't handle citations. Zotero doesn't collaborate in real-time. SyncScript bridges that gap—it's a collaborative research engine where teams build Knowledge Vaults together, instantly."

**Show:** Landing page briefly (your polished Bitcoin DeFi aesthetic will make an impression)

---

## 0:30-1:30 — Architecture Overview (60 sec)

**What judges want:** Optimized schema, many-to-many relationships, scaling plan

**Show your data model diagram and say:**

> "Our PostgreSQL schema handles complex research relationships through three core models:"

1. **Vaults** — The container (has owner, many members)
2. **VaultMemberships** — Many-to-many with role enum (Owner/Contributor/Viewer)
3. **Sources → Annotations** — Nested relationships with foreign keys

**Key phrase to use:**
> "This isn't a flat file system—it's a relational graph designed for national scale. Every query is indexed, every relationship is explicit."

**Flash the tech stack:**
- Django + DRF (battle-tested)
- PostgreSQL (relational integrity)
- Redis (caching + channels)
- Cloudflare R2 (S3-compatible, global CDN)

---

## 1:30-4:00 — Live Demo: The Money Shot (2.5 min)

**This is 50% of your score (Real-Time + UX).** Pre-stage everything.

### Demo Script:

**1. Login (15 sec)**
> "JWT authentication with secure httpOnly cookies. I'll log in as a researcher."

**2. Create a Vault (20 sec)**
> "I'm creating a new Knowledge Vault for our AI Ethics research project."

**3. Add a Source (30 sec)**
> "Let me add a research paper..."
- Paste a URL
- Show metadata auto-populating (if you have this)
- Upload a PDF to cloud storage

**4. THE REAL-TIME MOMENT (45 sec)** — Most important

> "Now watch this—I have a second browser open as a collaborator..."

- Add a source or annotation in Browser A
- **Instantly appears in Browser B** via WebSocket
- Say: "Zero refresh. Django Channels + Redis pub/sub. Every collaborator sees changes in under 100ms."

**5. Role-Based Views (20 sec)**
> "As a Viewer, I can read but the edit buttons disappear. The UI adapts to permissions dynamically."

**6. PDF Viewer (20 sec)**
> "PDFs are served via signed URLs from Cloudflare R2—immutable, secure, and globally distributed."

---

## 4:00-5:00 — Security Deep-Dive (60 sec)

**What judges want:** JWT, RBAC, rate-limiting, audit logs

**Show and tell:**

1. **JWT Auth**
   > "Access tokens expire in 15 minutes, refresh tokens in 7 days. Stored in httpOnly cookies—not localStorage."

2. **RBAC Demo**
   > "Three roles enforced at the API level. A Viewer literally cannot POST to the sources endpoint—Django returns 403."

3. **Rate Limiting**
   > "We use django-ratelimit backed by Redis. Abuse gets throttled before it hits the database."

4. **Audit Logs** (if you have this)
   > "Every action is logged immutably. Research integrity requires knowing who changed what and when."

---

## 5:00-6:00 — Creativity & Edge Features (60 sec)

**This differentiates you from other teams.** Pick 2-3:

| Feature | What to Say |
|---------|-------------|
| **AI Metadata Extraction** | "Claude API auto-extracts title, authors, and abstract from PDFs" |
| **Auto-Citation Generation** | "One click generates BibTeX or APA citations from any source URL" |
| **Inline PDF Viewer** | "Read and annotate PDFs without leaving the app" |
| **Smart Search** | "Full-text search across all sources using PostgreSQL trigrams" |
| **Notification System** | "Pusher integration sends real-time browser notifications when collaborators join" |

> "These aren't just nice-to-haves—they solve real researcher pain points."

---

## 6:00-7:00 — The Scale Story + Close (60 sec)

**End with confidence about scalability:**

> "This system is architected for national scale from day one:
> - Stateless backend → horizontal scaling
> - Redis caching → sub-millisecond reads
> - Cloudflare R2 → global file delivery
> - WebSocket channels → real-time at any user count
> - Celery workers → async task processing"

**Final statement:**

> "SyncScript isn't a bookmarking tool with extra features. It's a high-concurrency collaborative engine that treats research integrity as a first-class citizen. Thank you."

---

## Pre-Demo Checklist

- [ ] Two browser windows open (different users logged in)
- [ ] Test WebSocket connection is live
- [ ] Have a PDF ready to upload
- [ ] Have a URL ready to paste
- [ ] Clear any test data that looks messy
- [ ] Database has some realistic seed data
- [ ] Verify R2/S3 uploads are working

---

## Q&A Prep — Likely Questions

| Question | Strong Answer |
|----------|---------------|
| "How do you handle concurrent edits?" | "Optimistic locking with version fields. Conflicts surface to the user rather than silent overwrites." |
| "Why Django over Node/Go?" | "DRF is battle-tested for complex data relationships. Django Channels handles WebSockets natively. We chose reliability over hype." |
| "How would you scale to 100K users?" | "Horizontal pod scaling, Redis cluster, read replicas for PostgreSQL, CDN for static assets." |
| "What's your caching strategy?" | "Cache vault listings and permission checks in Redis. Invalidate on writes via Django signals." |
| "How do you ensure file immutability?" | "Signed URLs with expiration. Files in R2 are versioned and never overwritten." |

---

## Pro Tips

1. **Practice the WebSocket demo 5 times** — This is your "wow" moment
2. **Don't read from slides** — The demo IS your slides
3. **Use technical terms confidently** — "Pub/sub", "signed URLs", "JWT refresh rotation"
4. **If something breaks, pivot** — Have a backup screen recording
5. **Make eye contact when explaining architecture** — Show you understand it deeply

---

Good luck—your stack is solid. Now just show it off.
