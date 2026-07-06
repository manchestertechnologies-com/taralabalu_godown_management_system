import os
import urllib.parse
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from datetime import datetime
import sqlite3
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.secret_key = 'taralabalu_secret_key_87924'

# User credentials dictionary (Default password for all is 123)
USERS = {
    "head": {"password": "123", "role": "head", "inst_id": None, "name": "Head Office / ಸಂಸ್ಥೆಯ ಮುಖ್ಯಸ್ಥರು"},
    "godown": {"password": "123", "role": "godown", "inst_id": None, "name": "Central Godown Clerk / ಗೋದಾಮು ಗುಮಾಸ್ತ"},
    "boyshostel": {"password": "123", "role": "hostel", "inst_id": 1, "name": "Stores - Boys Hostel"},
    "girlshostel": {"password": "123", "role": "hostel", "inst_id": 2, "name": "Stores - Girls Hostel"},
    "math": {"password": "123", "role": "hostel", "inst_id": 3, "name": "Stores - Math"},
    "shantivanabidara": {"password": "123", "role": "hostel", "inst_id": 4, "name": "Stores - Shantivana Bidara"},
    "shantivanagurukula": {"password": "123", "role": "hostel", "inst_id": 5, "name": "Stores - Shantivana Gurukula"},
    "sirigerebhs": {"password": "123", "role": "hostel", "inst_id": 6, "name": "Stores - Sirigere BHS"},
    "sirigereghs": {"password": "123", "role": "hostel", "inst_id": 7, "name": "Stores - Sirigere GHS"},
    "storesa": {"password": "123", "role": "hostel", "inst_id": 8, "name": "Stores - A"},
    "aooffice": {"password": "123", "role": "hostel", "inst_id": 9, "name": "Stores - AO_Office"},
    "shraddajali": {"password": "123", "role": "hostel", "inst_id": 10, "name": "Store - Shraddhajali"}
}


# Supabase Connection String (Default)
SUPABASE_URL = "postgresql://postgres:Bery8792480218@db.rsvkrseaxewamlipnuku.supabase.co:5432/postgres"

# Mapping of Inst_ID to its corresponding stock column name in Grocery_Items table
INST_ID_TO_COLUMN = {
    1: "Boys_Hostel_Qty",      # Stores - Boys Hostel
    2: "Girls_Hostel_Qty",     # Stores - Girls Hostel
    3: "Math_Qty",             # Stores - Math
    4: "Shantivan_Qty_a",      # Stores - Shantivana Bidara
    5: "Shantivan_Qty_a",      # Stores - Shantivana Gurukula
    6: "Boys_Hostel_Qty",      # Stores - Sirigere BHS
    7: "Girls_Hostel_Qty",     # Stores - Sirigere GHS
    8: "Hunnime_Qty",          # Stores - A
    9: "AO_Office_Qty",        # Stores - AO_Office
    10: "Shraddanjali_Qty"     # Store - Shraddhajali
}


def get_db_connection():
    # Only connect to PostgreSQL if DATABASE_URL is defined (Production/Render)
    if 'DATABASE_URL' in os.environ:
        conn_str = os.environ['DATABASE_URL']
        conn_str = conn_str.replace(":[Bery8792480218]@", ":Bery8792480218@")
        try:
            result = urllib.parse.urlparse(conn_str)
            username = result.username
            password = result.password
            database = result.path[1:]
            hostname = result.hostname
            port = result.port
            
            conn = psycopg2.connect(
                database=database,
                user=username,
                password=password,
                host=hostname,
                port=port,
                connect_timeout=3
            )
            return conn, "postgresql"
        except Exception as e:
            # Fallback to local SQLite using absolute path
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, 'database.db')
            conn = sqlite3.connect(db_path)
            return conn, "sqlite"
    else:
        # Locally: Always use SQLite database (database.db)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'database.db')
        conn = sqlite3.connect(db_path)
        return conn, "sqlite"


def db_query(query, args=(), fetch=True):
    conn, db_type = get_db_connection()
    
    # Translate psycopg2 placeholder '%s' to sqlite3 placeholder '?' if needed
    if db_type == "sqlite":
        query = query.replace("%s", "?")
        
    cursor = conn.cursor()
    try:
        cursor.execute(query, args)
        if fetch:
            if db_type == "postgresql":
                # For PostgreSQL, get column names from description
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    result = [dict(zip(columns, row)) for row in rows]
                else:
                    result = []
            else:
                # For SQLite, manually structure
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    result = [dict(zip(columns, row)) for row in rows]
                else:
                    result = []
            cursor.close()
            conn.close()
            return result
        else:
            conn.commit()
            cursor.close()
            conn.close()
            return None
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        raise e

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/login')
@app.route('/login/<slug>')
def login_page(slug=None):
    if 'username' in session:
        return redirect(url_for('index'))
    return render_template('login.html', preselected_slug=slug)

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')
    
    if username in USERS and USERS[username]['password'] == password:
        session['username'] = username
        session['role'] = USERS[username]['role']
        session['inst_id'] = USERS[username]['inst_id']
        session['name'] = USERS[username]['name']
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


# --- API ENDPOINTS ---

# 1. Master Grocery Items List
@app.route('/api/grocery-items', methods=['GET'])
def get_grocery_items():
    items = db_query("SELECT * FROM Grocery_Items ORDER BY Grocery_Code")
    return jsonify(items)

@app.route('/api/grocery-items', methods=['POST'])
def add_grocery_item():
    data = request.json
    code = data.get('Grocery_Code')
    name_kan = data.get('Grocery_Items_Kan')
    name_eng = data.get('Grocery_Items_Eng')
    category = data.get('Grocery_Category')
    cat_code = data.get('Category_Code')
    rate = data.get('Std_Rate', 0.0)
    unit = data.get('Qtl_Kg_Ltr')
    remarks = data.get('Remarks', '')
    
    if not code or not name_kan or not unit:
        return jsonify({'error': 'ಕೋಡ್, ಕನ್ನಡ ಹೆಸರು ಮತ್ತು ಘಟಕ ಕಡ್ಡಾಯವಾಗಿದೆ (Code, Kannada name and unit are required)'}), 400
        
    try:
        db_query("""
            INSERT INTO Grocery_Items 
            (Grocery_Code, Grocery_Items_Kan, Grocery_Items_Eng, Grocery_Category, Category_Code, Std_Rate, Qtl_Kg_Ltr, Remarks, DateStamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (code, name_kan, name_eng, category, cat_code, rate, unit, remarks, datetime.now().strftime('%Y-%m-%d')))
    except Exception as e:
        return jsonify({'error': f'ದಾಖಲಿಸುವಲ್ಲಿ ದೋಷ: {str(e)}'}), 400
        
    return jsonify({'success': True})

@app.route('/api/grocery-items/<int:code>', methods=['DELETE'])
def delete_grocery_item(code):
    if 'role' not in session or session['role'] != 'head':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        db_query("DELETE FROM Grocery_Items WHERE Grocery_Code = %s", (code,), fetch=False)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# 2. Institutions List
@app.route('/api/institutions', methods=['GET'])
def get_institutions():
    insts = db_query("SELECT * FROM Institutions ORDER BY Inst_ID")
    return jsonify(insts)

# 3. Shops & Donors List
@app.route('/api/donors', methods=['GET'])
def get_donors():
    donors = db_query("SELECT * FROM Shops_Donors ORDER BY Shop_Donor_ID")
    return jsonify(donors)

@app.route('/api/donors', methods=['POST'])
def add_donor():
    data = request.json
    donor_id = data.get('Shop_Donor_ID')
    name = data.get('Shop_Donor_Name')
    place = data.get('Place')
    mobile = data.get('Mobile')
    remarks = data.get('Remarks')
    
    if not donor_id or not name:
        return jsonify({'error': 'ಐಡಿ ಮತ್ತು ಹೆಸರು ಕಡ್ಡಾಯವಾಗಿದೆ (ID and name are required)'}), 400
        
    try:
        db_query("""
            INSERT INTO Shops_Donors 
            (Year1, Shop_Donor_ID, Shop_Donor_Name, Place, Mobile, Remarks, DateStamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, ('2026', donor_id, name, place, mobile, remarks, datetime.now().strftime('%Y-%m-%d')))
    except Exception as e:
        return jsonify({'error': f'ದೋಷ: {str(e)}'}), 400
        
    return jsonify({'success': True})

# 4. Stock Inward (Godown Stocking from Donors)
@app.route('/api/godown-stock', methods=['GET'])
def get_godown_stock():
    logs = db_query("""
        SELECT si.Rec, si.Date1, si.Grocery_Code, gi.Grocery_Items_Kan, gi.Qtl_Kg_Ltr,
               si.Stock, sd.Shop_Donor_Name, si.Remarks, si.Purchased_Donation
        FROM Stock_Issue si
        JOIN Grocery_Items gi ON si.Grocery_Code = gi.Grocery_Code
        LEFT JOIN Shops_Donors sd ON si.Shop_Donor_ID = sd.Shop_Donor_ID
        WHERE si.Stock > 0
        ORDER BY si.Rec DESC
    """)
    return jsonify(logs)

@app.route('/api/godown-stock', methods=['POST'])
def add_godown_stock():
    data = request.json
    code = data.get('Grocery_Code')
    donor_id = data.get('Shop_Donor_ID')
    quantity = data.get('Quantity')
    rate = data.get('Purchase_Rate', 0.0)
    type_inward = data.get('Purchased_Donation', 'Donation') # 'Purchase' or 'Donation'
    remarks = data.get('Remarks', '')
    date_str = data.get('Date') or datetime.now().strftime('%Y-%m-%d')
    
    if not code or not donor_id or not quantity:
        return jsonify({'error': 'ಎಲ್ಲಾ ವಿವರಗಳನ್ನು ಭರ್ತಿ ಮಾಡಿ (Please fill all details)'}), 400
        
    try:
        qty = float(quantity)
        rate = float(rate)
        if qty <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'error': 'ಪ್ರಮಾಣ ಸರಿಯಾದ ಸಂಖ್ಯೆಯಾಗಿರಬೇಕು (Quantity must be a positive number)'}), 400
        
    # Transactional Update
    try:
        # 1. Log inward stock in Stock_Issue
        db_query("""
            INSERT INTO Stock_Issue 
            (Year1, Date1, Grocery_Code, Shop_Donor_ID, Purchase_Rate, Purchase_Amount, Stock, Issue, Remarks, Purchased_Donation, DateStamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, ('2026', date_str, code, donor_id, rate, qty * rate, qty, 0.0, remarks, type_inward, datetime.now().strftime('%Y-%m-%d %H:%M:%S')), fetch=False)
        
        # 2. Increment Tot_Stock in Grocery_Items
        db_query("""
            UPDATE Grocery_Items 
            SET Tot_Stock = Tot_Stock + %s 
            WHERE Grocery_Code = %s
        """, (qty, code), fetch=False)
        
    except Exception as e:
        return jsonify({'error': f'ದೋಷ: {str(e)}'}), 500
        
    return jsonify({'success': True})

# 5. Indents & Transfers (Godown -> Hostels)
@app.route('/api/indents', methods=['GET'])
def get_indents():
    hostel_id = request.args.get('hostel_id')
    if hostel_id:
        logs = db_query("""
            SELECT ind.Rec, ind.Indent_Date, ind.Grocery_Code, gi.Grocery_Items_Kan, gi.Qtl_Kg_Ltr,
                   ind.Quantity, ind.Sanctioned_Quantity, ind.Sanctioned, ind.Sanctioned_on,
                   ind.Indent_no, ind.Remarks, inst.Institution
            FROM Indents ind
            JOIN Grocery_Items gi ON ind.Grocery_Code = gi.Grocery_Code
            JOIN Institutions inst ON ind.Inst_ID = inst.Inst_ID
            WHERE ind.Inst_ID = %s
            ORDER BY ind.Rec DESC
        """, (hostel_id,))
    else:
        logs = db_query("""
            SELECT ind.Rec, ind.Indent_Date, ind.Grocery_Code, gi.Grocery_Items_Kan, gi.Qtl_Kg_Ltr,
                   ind.Quantity, ind.Sanctioned_Quantity, ind.Sanctioned, ind.Sanctioned_on,
                   ind.Indent_no, ind.Remarks, inst.Institution, ind.Inst_ID
            FROM Indents ind
            JOIN Grocery_Items gi ON ind.Grocery_Code = gi.Grocery_Code
            JOIN Institutions inst ON ind.Inst_ID = inst.Inst_ID
            ORDER BY ind.Rec DESC
        """)
    return jsonify(logs)

@app.route('/api/indents', methods=['POST'])
def create_indent():
    data = request.json
    inst_id = data.get('Inst_ID')
    code = data.get('Grocery_Code')
    quantity = data.get('Quantity')
    remarks = data.get('Remarks', '')
    indent_no = f"IND-{datetime.now().strftime('%M%S')}"
    
    if not inst_id or not code or not quantity:
        return jsonify({'error': 'ಎಲ್ಲಾ ವಿವರಗಳನ್ನು ಭರ್ತಿ ಮಾಡಿ (Please fill all details)'}), 400
        
    try:
        qty = float(quantity)
        if qty <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'error': 'ಪ್ರಮಾಣ ಸರಿಯಾದ ಸಂಖ್ಯೆಯಾಗಿರಬೇಕು (Quantity must be a positive number)'}), 400
        
    try:
        db_query("""
            INSERT INTO Indents
            (Year1, Indent_Date, Grocery_Code, Inst_ID, Quantity, Indent_no, Sanctioned, Remarks, DateStamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, ('2026', datetime.now().strftime('%Y-%m-%d'), code, inst_id, qty, indent_no, 'Pending', remarks, datetime.now().strftime('%Y-%m-%d')), fetch=False)
    except Exception as e:
        return jsonify({'error': f'ದೋಷ: {str(e)}'}), 500
        
    return jsonify({'success': True})

# Approve & Issue Indent (Godown Action)
@app.route('/api/indents/<int:indent_rec>/approve', methods=['POST'])
def approve_indent(indent_rec):
    data = request.json or {}
    sanctioned_qty = data.get('Sanctioned_Quantity')
    
    # Fetch original indent
    indents = db_query("SELECT * FROM Indents WHERE Rec = %s", (indent_rec,))
    if not indents:
        return jsonify({'error': 'ಇಂಡೆಂಟ್ ವಿವರ ಸಿಕ್ಕಿಲ್ಲ (Indent not found)'}), 404
    indent = indents[0]
    
    if indent['Sanctioned'] != 'Pending':
        return jsonify({'error': 'ಈ ಇಂಡೆಂಟ್ ಈಗಾಗಲೇ ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲಾಗಿದೆ (This indent is already processed)'}), 400
        
    if sanctioned_qty is None:
        sanctioned_qty = indent['Quantity']
        
    try:
        sanctioned_qty = float(sanctioned_qty)
        if sanctioned_qty <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'error': 'ಅನುಮೋದಿಸಿದ ಪ್ರಮಾಣ ಸರಿಯಾಗಿಲ್ಲ (Sanctioned quantity is invalid)'}), 400
        
    # Check godown stock availability
    code = indent['Grocery_Code']
    items = db_query("SELECT Tot_Stock, Std_Rate FROM Grocery_Items WHERE Grocery_Code = %s", (code,))
    if not items:
        return jsonify({'error': 'ವಸ್ತು ಪಟ್ಟಿಯಲ್ಲಿಲ್ಲ (Item not in master list)'}), 404
    item = items[0]
    
    if item['Tot_Stock'] < sanctioned_qty:
        return jsonify({'error': f'ಗೋದಾಮಿನಲ್ಲಿ ಸಾಕಷ್ಟು ದಾಸ್ತಾನು ಇಲ್ಲ. ಲಭ್ಯವಿರುವುದು: {item["Tot_Stock"]} (Insufficient godown stock. Available: {item["Tot_Stock"]})'}), 400
        
    # Transactional Update
    try:
        # 1. Update Indent status
        db_query("""
            UPDATE Indents
            SET Sanctioned_Quantity = %s, Sanctioned = 'Sent', Sanctioned_on = %s
            WHERE Rec = %s
        """, (sanctioned_qty, datetime.now().strftime('%Y-%m-%d'), indent_rec), fetch=False)
        
        # 2. Log Issue in Stock_Issue
        rate = item['Std_Rate'] or 0.0
        db_query("""
            INSERT INTO Stock_Issue
            (Year1, Date1, Grocery_Code, Issue_Inst_ID, Issue, Issue_Amount, Remarks, Purchased_Donation, DateStamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, ('2026', datetime.now().strftime('%Y-%m-%d'), code, indent['Inst_ID'], sanctioned_qty, sanctioned_qty * rate, f"Approved Indent {indent['Indent_no']}", 'Issue', datetime.now().strftime('%Y-%m-%d')), fetch=False)
        
        # 3. Deplete Godown stock
        db_query("""
            UPDATE Grocery_Items
            SET Tot_Stock = Tot_Stock - %s, Tot_Issue = Tot_Issue + %s
            WHERE Grocery_Code = %s
        """, (sanctioned_qty, sanctioned_qty, code), fetch=False)
        
    except Exception as e:
        return jsonify({'error': f'ದೋಷ: {str(e)}'}), 500
        
    return jsonify({'success': True})

# Acknowledge Delivery (Hostel Action)
@app.route('/api/indents/<int:indent_rec>/acknowledge', methods=['POST'])
def acknowledge_indent(indent_rec):
    indents = db_query("SELECT * FROM Indents WHERE Rec = %s", (indent_rec,))
    if not indents:
        return jsonify({'error': 'ದಾಖಲೆ ಸಿಕ್ಕಿಲ್ಲ (Record not found)'}), 404
    indent = indents[0]
    
    if indent['Sanctioned'] == 'Received':
        return jsonify({'error': 'ಈಗಾಗಲೇ ಸ್ವೀಕರಿಸಲಾಗಿದೆ (Already acknowledged)'}), 400
        
    inst_id = indent['Inst_ID']
    code = indent['Grocery_Code']
    qty = indent['Sanctioned_Quantity']
    
    column_name = INST_ID_TO_COLUMN.get(inst_id)
    if not column_name:
        return jsonify({'error': 'ಈ ವಸತಿ ನಿಲಯಕ್ಕೆ ದಾಸ್ತಾನು ವಿಭಾಗ ಹೊಂದಿಕೆಯಾಗುತ್ತಿಲ್ಲ (Unmapped institution)'}), 400
        
    # Transactional Update
    try:
        # 1. Update Indents to Received
        db_query("""
            UPDATE Indents
            SET Sanctioned = 'Received', Sanctioned_on = %s
            WHERE Rec = %s
        """, (datetime.now().strftime('%Y-%m-%d'), indent_rec), fetch=False)
        
        # 2. Increment targeted column in Grocery_Items
        db_query(f"""
            UPDATE Grocery_Items
            SET {column_name} = {column_name} + %s
            WHERE Grocery_Code = %s
        """, (qty, code), fetch=False)
        
    except Exception as e:
        return jsonify({'error': f'ದೋಷ: {str(e)}'}), 500
        
    return jsonify({'success': True})

# 6. Hostel Stock Balance
@app.route('/api/hostel-stock/<int:inst_id>', methods=['GET'])
def get_hostel_stock(inst_id):
    column_name = INST_ID_TO_COLUMN.get(inst_id)
    if not column_name:
        return jsonify([])
        
    # Fetch stock levels for that mapped column
    stock = db_query(f"""
        SELECT Grocery_Code, Grocery_Items_Kan, Qtl_Kg_Ltr, {column_name} AS CurrentBalance
        FROM Grocery_Items
        WHERE {column_name} >= 0
        ORDER BY Grocery_Code
    """)
    return jsonify(stock)

# 7. Daily Usage Logging (Hostel)
@app.route('/api/daily-usage', methods=['POST'])
def add_daily_usage():
    data = request.json
    inst_id = data.get('Inst_ID')
    code = data.get('Grocery_Code')
    quantity = data.get('Quantity')
    remarks = data.get('Remarks', 'ದೈನಂದಿನ ಅಡುಗೆ ಬಳಕೆ')
    date_str = data.get('Date') or datetime.now().strftime('%Y-%m-%d')
    
    if not inst_id or not code or not quantity:
        return jsonify({'error': 'ಎಲ್ಲಾ ವಿವರಗಳನ್ನು ಭರ್ತಿ ಮಾಡಿ (Please fill all details)'}), 400
        
    try:
        qty = float(quantity)
        if qty <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'error': 'ಪ್ರಮಾಣ ಸರಿಯಾದ ಸಂಖ್ಯೆಯಾಗಿರಬೇಕು (Quantity must be a positive number)'}), 400
        
    column_name = INST_ID_TO_COLUMN.get(inst_id)
    if not column_name:
        return jsonify({'error': 'ಅಮಾನ್ಯ ವಸತಿ ನಿಲಯ (Invalid hostel)'}), 400
        
    # Check if stock exists
    items = db_query(f"SELECT {column_name}, Std_Rate FROM Grocery_Items WHERE Grocery_Code = %s", (code,))
    if not items:
        return jsonify({'error': 'ವಸ್ತು ಸಿಕ್ಕಿಲ್ಲ (Item not found)'}), 404
    item = items[0]
    
    if item[column_name] < qty:
        return jsonify({'error': f'ಸಾಕಷ್ಟು ದಾಸ್ತಾನು ಇಲ್ಲ. ಲಭ್ಯವಿರುವುದು: {item[column_name]} (Insufficient stock. Available: {item[column_name]})'}), 400
        
    # Transactional Update
    try:
        # 1. Decrement target branch column in Grocery_Items
        db_query(f"""
            UPDATE Grocery_Items
            SET {column_name} = {column_name} - %s
            WHERE Grocery_Code = %s
        """, (qty, code), fetch=False)
        
        # 2. Log in Stock_Issue as a consumption log (DonorID is null, Issue is set)
        rate = item['Std_Rate'] or 0.0
        db_query("""
            INSERT INTO Stock_Issue
            (Year1, Date1, Grocery_Code, Issue_Inst_ID, Issue, Issue_Amount, Remarks, Purchased_Donation, DateStamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, ('2026', date_str, code, inst_id, qty, qty * rate, remarks, 'Consumption', datetime.now().strftime('%Y-%m-%d')), fetch=False)
        
    except Exception as e:
        return jsonify({'error': f'ದೋಷ: {str(e)}'}), 500
        
    return jsonify({'success': True})

@app.route('/api/daily-usage/<int:inst_id>', methods=['GET'])
def get_daily_usage_logs(inst_id):
    logs = db_query("""
        SELECT si.Rec, si.Date1, si.Grocery_Code, gi.Grocery_Items_Kan, gi.Qtl_Kg_Ltr,
               si.Issue AS QuantityUsed, si.Remarks
        FROM Stock_Issue si
        JOIN Grocery_Items gi ON si.Grocery_Code = gi.Grocery_Code
        WHERE si.Issue_Inst_ID = %s AND si.Purchased_Donation = 'Consumption'
        ORDER BY si.Rec DESC
    """, (inst_id,))
    return jsonify(logs)

# 8. Low Stock Alerts (Global across all hostels)
@app.route('/api/low-stock-alerts', methods=['GET'])
def get_low_stock_alerts():
    alerts = []
    
    # We inspect columns for each mapped institution
    for inst_id, col in INST_ID_TO_COLUMN.items():
        # Get institution name
        inst_rows = db_query("SELECT Institution FROM Institutions WHERE Inst_ID = %s", (inst_id,))
        if not inst_rows:
            continue
        inst_name = inst_rows[0]['Institution']
        
        low_items = db_query(f"""
            SELECT Grocery_Code, Grocery_Items_Kan, Qtl_Kg_Ltr, {col} AS CurrentBalance
            FROM Grocery_Items
            WHERE {col} < 10.0 AND {col} >= 0
        """)
        for item in low_items:
            alerts.append({
                'Inst_ID': inst_id,
                'Institution': inst_name,
                'Grocery_Code': item['Grocery_Code'],
                'Grocery_Items_Kan': item['Grocery_Items_Kan'],
                'Qtl_Kg_Ltr': item['Qtl_Kg_Ltr'],
                'CurrentBalance': item['CurrentBalance']
            })
            
    return jsonify(alerts)

# --- Vegetable Management API ---
@app.route('/api/vegetables', methods=['GET'])
def get_vegetables():
    inst_id = request.args.get('inst_id')
    if inst_id:
        logs = db_query("""
            SELECT v.*, i.Institution 
            FROM Vegetable v
            JOIN Institutions i ON v.Inst_ID = i.Inst_ID
            WHERE v.Inst_ID = %s
            ORDER BY v.Rec DESC
        """, (inst_id,))
    else:
        logs = db_query("""
            SELECT v.*, i.Institution 
            FROM Vegetable v
            JOIN Institutions i ON v.Inst_ID = i.Inst_ID
            ORDER BY v.Rec DESC
        """)
    return jsonify(logs)

@app.route('/api/vegetables', methods=['POST'])
def add_vegetable():
    data = request.json or {}
    try:
        db_query("""
            INSERT INTO Vegetable 
            (Inst_ID, Year1, Purchase_On, V_Code, Quantity, Bill_Date, Bill_No, Rate, Remarks, Issue_Place, Purchased_Donation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get('Inst_ID'),
            data.get('Year1', '2026'),
            data.get('Purchase_On'),
            data.get('V_Code'),
            data.get('Quantity', 0.0),
            data.get('Bill_Date'),
            data.get('Bill_No'),
            data.get('Rate', 0.0),
            data.get('Remarks'),
            data.get('Issue_Place'),
            data.get('Purchased_Donation', 'Purchase')
        ), fetch=False)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Bills and Payments API ---
@app.route('/api/bills', methods=['GET'])
def get_bills():
    logs = db_query("""
        SELECT b.*, sd.Shop_Donor_Name, sd.Place 
        FROM Bills b
        LEFT JOIN Shops_Donors sd ON b.Shop_Donor_ID = sd.Shop_Donor_ID
        ORDER BY b.Rec DESC
    """)
    return jsonify(logs)

@app.route('/api/bills', methods=['POST'])
def add_bill():
    data = request.json or {}
    try:
        db_query("""
            INSERT INTO Bills 
            (Year1, Shop_Donor_ID, Bill_Date, Bill_No, Bill_Amount, Paid_By, Ch_Date, Ch_No, Ch_Amount, Remarks, DateAdded)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get('Year1', '2026'),
            data.get('Shop_Donor_ID'),
            data.get('Bill_Date'),
            data.get('Bill_No'),
            data.get('Bill_Amount', 0.0),
            data.get('Paid_By'),
            data.get('Ch_Date'),
            data.get('Ch_No'),
            data.get('Ch_Amount', 0.0),
            data.get('Remarks'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ), fetch=False)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

