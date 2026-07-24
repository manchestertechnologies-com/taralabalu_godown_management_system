# ತರಳಬಾಳು ಗೋದಾಮು ಮತ್ತು ವಸತಿ ನಿಲಯ ದಾಸ್ತಾನು ನಿರ್ವಹಣಾ ವ್ಯವಸ್ಥೆ (Taralabalu Godown Management System)

A responsive, full-stack Inventory Management Web Application optimized for both mobile and desktop devices. It is designed for central warehouse (godown) staff and hostel clerks. The user interface, item names, logs, and generated receipts are in **Kannada**, while the underlying codebase and database schema remain in **English**.

---

## ಪ್ರಮುಖ ಲಕ್ಷಣಗಳು (Key Features)

1. **ಕೇಂದ್ರೀಕೃತ ಮುಖ್ಯ ಪಟ್ಟಿ (Centralized Master List)**:
   - Grocery items are managed inside the `Grocery_Items` table.
   - Only warehouse administrators can add items to prevent naming and code mismatches.

2. **ದ್ವಿಮುಖ ಪರಿಶೀಲನೆ ಮತ್ತು ಇಂಡೆಂಟ್ ವ್ಯವಸ್ಥೆ (Two-Way Handshake & Indents)**:
   - Hostels submit requests (**"ಇಂಡೆಂಟ್ ಸಲ್ಲಿಸು"**).
   - Central Godown approves and issues the items (**"ಅನುಮೋದಿಸು & ಕಳುಹಿಸು"**). This immediately depletes godown stock and places the transfer in **"ಕಳುಹಿಸಲಾಗಿದೆ" (Sent)** status.
   - The receiving hostel must click **"ಸ್ವೀಕೃತಿ ದೃಢೀಕರಿಸು" (Acknowledge Receipt)** to change the status to **"ಸ್ವೀಕರಿಸಲಾಗಿದೆ" (Received)**.
   - Once acknowledged, the quantity automatically increments the hostel's specific stock column in `Grocery_Items`.

3. **ಸ್ವಯಂಚಾಲಿತ ಸಿಂಕ್ (Automated Inventory Sync)**:
   - Stock balances are mapped directly to columns in the `Grocery_Items` table:
     - *Boys Hostel / Sirigere BHS* $\rightarrow$ `Boys_Hostel_Qty`
     - *Girls Hostel / Sirigere GHS* $\rightarrow$ `Girls_Hostel_Qty`
     - *Math* $\rightarrow$ `Math_Qty`
     - *Shantivana Bidara / Shantivana Gurukula* $\rightarrow$ `Shantivan_Qty_a`
     - *AO_Office* $\rightarrow$ `AO_Office_Qty`
     - *Shraddhajali* $\rightarrow$ `Shraddanjali_Qty`
     - *Others* $\rightarrow$ `Hunnime_Qty`

4. **ಬಳಕೆ ಮತ್ತು ಕೊರತೆ ಎಚ್ಚರಿಕೆ (Daily Usage & Low Stock Alerts)**:
   - Hostel clerks log daily consumption, which depletes their specific stock column.
   - If stock levels fall below **10 units**, a pulsing red alert triggers on the dashboard.

5. **ಸ್ವೀಕೃತಿ ರಸೀದಿ (Receipt Generation)**:
   - Hostel clerks can instantly open and print/save an official acknowledgment receipt in Kannada detailing quantities, dates, and sign-off lines.

---

## ತಂತ್ರಜ್ಞಾನಗಳು (Technology Stack)

* **Frontend**: HTML, CSS, JavaScript, Tailwind CSS (Mobile-First responsive layout)
* **Backend**: Python 3, Flask
* **Database**: PostgreSQL (Supabase) with local SQLite fallback (`database.db`) if Supabase is offline.

---

## ತ್ವರಿತ ಚಾಲನಾ ಮಾರ್ಗದರ್ಶಿ (How to Run Locally)

Follow these steps to run the application on your local machine:

### 1. ವರ್ಚುವಲ್ ಎನ್ವಿರಾನ್ಮೆಂಟ್ ರಚಿಸಿ (Setup Virtual Environment)
Open your terminal/command prompt in the project directory and run:
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 2. ಡಿಪೆಂಡೆನ್ಸಿಗಳನ್ನು ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಿ (Install Dependencies)
```bash
pip install -r requirements.txt
```

### 3. ಡೇಟಾಬೇಸ್ ಅನ್ನು ಪ್ರಾರಂಭಿಸಿ (Initialize PostgreSQL / SQLite)
This script creates the exact 7 tables and populates them with seed data. It tries to connect to Supabase first; if Supabase is offline or DNS fails, it automatically seeds a local SQLite database (`database.db`) so you can run the app immediately:
```bash
python init_db.py
```

### 4. ಸರ್ವರ್ ಅನ್ನು ರನ್ ಮಾಡಿ (Start the Flask Server)
```bash
python app.py
```
After starting, open your browser and navigate to:
👉 **[http://localhost:5000](http://localhost:5000)**

---

## ಡೇಟಾಬೇಸ್ ವಿವರಗಳು (Database Schema)

We implement the exact 7-table schema requested:
* **Grocery_Items**: Master list and branch quantities (`Rec`, `Grocery_Code`, `Grocery_Items_Kan`, `Grocery_Items_Eng`, `Grocery_Category`, `Std_Rate`, `Qtl_Kg_Ltr`, branch quantity columns like `Boys_Hostel_Qty`, etc.)
* **Stock_Issue**: Tracks all stock movements (Inwards, Issues, and Daily Consumption).
* **Indents**: Handshake vehicle for transfers (`Sanctioned` state: `Pending` $\rightarrow$ `Sent` $\rightarrow$ `Received`).
* **Institutions**: Mapped institutions.
* **Shops_Donors**: Register of vendors and donors.
* **Vegetable** & **Bills**: Financial logging.
