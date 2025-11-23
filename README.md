# MGLTickets

**MGLTickets** is a simple and intuitive **event ticket booking app**. It helps users discover events, view details, and book tickets online, while allowing organizers to manage their events efficiently.

---

## Features (MVP)

- 🗓️ Browse upcoming events  
- 📄 View event details and ticket types  
- 🎫 Book tickets online  
- 👤 User registration & authentication  
- 🛠️ Basic admin panel for event management

---

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL  
- **Frontend:** React, Vite, Tailwind CSS  
- **Authentication:** JWT tokens  
- **Deployment:** Render / Vercel (development), VPS planned

---

## Getting Started

### Prerequisites
- Python 3.10+  
- Node.js 18+  
- PostgreSQL 12+

---

## Backend Setup

```bash
# Clone the repo
git clone https://github.com/jmodhiambo/mgltickets.git
cd mgltickets/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt

# Create all tables defined in the model
alembic upgrade head

# Start the FastAPI server
uvicorn app.main:app --reload
```

---

## Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```

---

## Project Structure

```bash
mgltickets/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── core/                   # Config, security, settings
│   │   ├── cli/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── dependencies.py
│   │   ├── db/
│   │   │   ├── models/
│   │   │   ├── session.py
│   │   │   └── repositories/
│   │   ├── services/
│   │   ├── logs
│   │   ├── schemas/                # Pydantic models
│   │   ├── tests/
│   │   └── utils/
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── pages/
│   ├── services
│   └── ...
├── README.md
└── ...
```

---

## Future Plans

- Payment integration (M-Pesa, Stripe)
- Multi-event support per organizer
- Event flyer uploads & management
- Email notifications for bookings
- Analytics dashboard for organizers

---

## License

This project is licensed under the MIT License.