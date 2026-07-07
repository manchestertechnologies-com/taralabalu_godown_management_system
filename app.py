import os
import urllib.parse
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from datetime import datetime
import sqlite3
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.secret_key = 'taralabalu_secret_key_87924'

USERS = {
    "head": {"password": "123", "role": "head", "inst_id": None, "name": "Admin / ಸಂಸ್ಥೆಯ ಆಡಳಿತಗಾರರು"},
    "godown": {"password": "123", "role": "godown", "inst_id": None, "name": "Central Godown Clerk / ಗೋದಾಮು ಗುಮಾಸ್ತ"},
    "accounts": {"password": "123", "role": "accounts", "inst_id": None, "name": "Accounts / ಲೆಕ್ಕಾಧಿಕಾರಿ"},
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

INST_ID_TO_COLUMN = {
    1: "Boys_Hostel_Qty", 2: "Girls_Hostel_Qty", 3: "Math_Qty",
    4: "Shantivan_Qty_a", 5: "Shantivan_Qty_a", 6: "Boys_Hostel_Qty",
    7: "Girls_Hostel_Qty", 8: "Hunnime_Qty", 9: "AO_Office_Qty", 10: "Shraddanjali_Qty"
}


def get_db_connection():
    if 'DATABASE_URL' in os.environ:
        conn_str = os.environ['DATABASE_URL']
        conn_str = conn_str.replace(":[Bery8792480218]@", ":Bery8792480218@")
        try:
            result = urllib.parse.urlparse(conn_str)
            conn = psycopg2.connect(
                database=result.path[1:], user=result.username, password=result.password,
                host=result.hostname, port=result.port, connect_timeout=3)
            return conn, "postgresql"
        except Exception:
            pass
    base_dir = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(os.path.join(base_dir, 'database.db'))
    return conn, "sqlite"


def db_query(query, args=(), fetch=True):
    conn, db_type = get_db_connection()
    if db_type == "sqlite":
        query = query.replace("%s", "?")
    cursor = conn.cursor()
    try:
        cursor.execute(query, args)
        if fetch:
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                result = [dict(zip(columns, row)) for row in cursor.fetchall()]
            else:
                result = []
            cursor.close(); conn.close()
            return result
        else:
            conn.commit(); cursor.close(); conn.close()
            return None
    except Exception as e:
        conn.rollback(); cursor.close(); conn.close()
        raise e


def log_audit(module, action, target_id='', old_val='', new_val=''):
    try:
        username = session.get('username', 'system')
        db_query("INSERT INTO Audit_Logs (Timestamp,Username,Module,Action,Target_ID,Old_Value,New_Value) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), username, module, action, str(target_id), str(old_val)[:500], str(new_val)[:500]), fetch=False)
    except Exception:
        pass


def chk(*roles):
    return 'role' in session and session['role'] in roles


# --- PAGES ---

@app.route('/')
def index():
    if 'username' not in session: return redirect(url_for('login_page'))
    return render_template('index.html')

@app.route('/login')
@app.route('/login/<slug>')
def login_page(slug=None):
    if 'username' in session: return redirect(url_for('index'))
    return render_template('login.html', preselected_slug=slug)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


# --- AUTH ---

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')
    try:
        users = db_query("SELECT * FROM Users WHERE username = %s", (username,))
        if users and users[0]['password'] == password:
            u = users[0]
            session.update({'username': u['username'], 'role': u['role'], 'inst_id': u['inst_id'], 'name': u['name']})
            log_audit('Auth', 'Login', username)
            return jsonify({'success': True})
    except Exception:
        if username in USERS and USERS[username]['password'] == password:
            session.update({'username': username, 'role': USERS[username]['role'],
                            'inst_id': USERS[username]['inst_id'], 'name': USERS[username]['name']})
            return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


# --- GROCERY ITEMS ---

@app.route('/api/grocery-items', methods=['GET'])
def get_grocery_items():
    return jsonify(db_query("SELECT * FROM Grocery_Items ORDER BY Grocery_Code"))

@app.route('/api/grocery-items', methods=['POST'])
def add_grocery_item():
    if not chk('head', 'godown'): return jsonify({'error': 'Unauthorized'}), 403
    d = request.json or {}
    code, name_kan = d.get('Grocery_Code'), d.get('Grocery_Items_Kan')
    if not code or not name_kan: return jsonify({'error': 'Code and Kannada name required'}), 400
    try:
        db_query("INSERT INTO Grocery_Items (Grocery_Code,Grocery_Items_Kan,Grocery_Items_Eng,Grocery_Category,Category_Code,Std_Rate,Qtl_Kg_Ltr,Remarks,DateStamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (code, name_kan, d.get('Grocery_Items_Eng',''), d.get('Grocery_Category',''), d.get('Category_Code',''), d.get('Std_Rate',0.0), d.get('Qtl_Kg_Ltr','Kg'), d.get('Remarks',''), datetime.now().strftime('%Y-%m-%d')), fetch=False)
        log_audit('Items', 'Add', code, '', name_kan)
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 400

@app.route('/api/grocery-items/<int:code>', methods=['PUT'])
def edit_grocery_item(code):
    if not chk('head', 'godown'): return jsonify({'error': 'Unauthorized'}), 403
    d = request.json or {}
    try:
        db_query("UPDATE Grocery_Items SET Grocery_Items_Kan=%s,Grocery_Items_Eng=%s,Grocery_Category=%s,Category_Code=%s,Std_Rate=%s,Qtl_Kg_Ltr=%s,Remarks=%s WHERE Grocery_Code=%s",
            (d.get('Grocery_Items_Kan'), d.get('Grocery_Items_Eng',''), d.get('Grocery_Category',''), d.get('Category_Code',''), d.get('Std_Rate',0.0), d.get('Qtl_Kg_Ltr','Kg'), d.get('Remarks',''), code), fetch=False)
        log_audit('Items', 'Edit', code, '', d.get('Grocery_Items_Kan'))
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/grocery-items/<int:code>', methods=['DELETE'])
def delete_grocery_item(code):
    if not chk('head'): return jsonify({'error': 'Unauthorized'}), 403
    try:
        db_query("DELETE FROM Grocery_Items WHERE Grocery_Code = %s", (code,), fetch=False)
        log_audit('Items', 'Delete', code)
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500


# --- INSTITUTIONS ---

@app.route('/api/institutions', methods=['GET'])
def get_institutions():
    return jsonify(db_query("SELECT * FROM Institutions ORDER BY Inst_ID"))

@app.route('/api/institutions', methods=['POST'])
def add_institution():
    if not chk('head'): return jsonify({'error': 'Unauthorized'}), 403
    name = (request.json or {}).get('Institution', '').strip()
    if not name: return jsonify({'error': 'Name required'}), 400
    try:
        db_query("INSERT INTO Institutions (Institution) VALUES (%s)", (name,), fetch=False)
        log_audit('Institutions', 'Add', '', '', name)
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500


# --- DONORS ---

@app.route('/api/donors', methods=['GET'])
def get_donors():
    return jsonify(db_query("SELECT * FROM Shops_Donors ORDER BY Shop_Donor_Name"))

@app.route('/api/donors', methods=['POST'])
def add_donor():
    if not chk('head','godown','accounts'): return jsonify({'error':'Unauthorized'}), 403
    d = request.json or {}
    if not d.get('Shop_Donor_ID') or not d.get('Shop_Donor_Name'): return jsonify({'error':'ID and name required'}), 400
    try:
        db_query("INSERT INTO Shops_Donors (Year1,Shop_Donor_ID,Shop_Donor_Name,Place,Mobile,Remarks,DateStamp) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (datetime.now().year, d['Shop_Donor_ID'], d['Shop_Donor_Name'], d.get('Place',''), d.get('Mobile',''), d.get('Remarks',''), datetime.now().strftime('%Y-%m-%d')), fetch=False)
        log_audit('Donors', 'Add', d['Shop_Donor_ID'], '', d['Shop_Donor_Name'])
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 400

@app.route('/api/donors/<donor_id>', methods=['PUT'])
def edit_donor(donor_id):
    if not chk('head','godown','accounts'): return jsonify({'error':'Unauthorized'}), 403
    d = request.json or {}
    try:
        db_query("UPDATE Shops_Donors SET Shop_Donor_Name=%s,Place=%s,Mobile=%s,Remarks=%s WHERE Shop_Donor_ID=%s",
            (d.get('Shop_Donor_Name'), d.get('Place',''), d.get('Mobile',''), d.get('Remarks',''), donor_id), fetch=False)
        log_audit('Donors', 'Edit', donor_id, '', d.get('Shop_Donor_Name'))
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/donors/<donor_id>', methods=['DELETE'])
def delete_donor(donor_id):
    if not chk('head'): return jsonify({'error':'Unauthorized'}), 403
    try:
        db_query("DELETE FROM Shops_Donors WHERE Shop_Donor_ID = %s", (donor_id,), fetch=False)
        log_audit('Donors', 'Delete', donor_id)
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500


# --- STOCK INWARD ---

@app.route('/api/godown-stock', methods=['GET'])
def get_godown_stock():
    df = request.args.get('from',''); dt = request.args.get('to',''); dn = request.args.get('donor','')
    wheres = ["si.Stock > 0"]; args = []
    if df: wheres.append("si.Date1 >= %s"); args.append(df)
    if dt: wheres.append("si.Date1 <= %s"); args.append(dt)
    if dn: wheres.append("si.Shop_Donor_ID = %s"); args.append(dn)
    logs = db_query(f"""SELECT si.Rec,si.Date1,si.Grocery_Code,gi.Grocery_Items_Kan,gi.Grocery_Items_Eng,
        gi.Qtl_Kg_Ltr,si.Stock,si.Purchase_Rate,(si.Stock*si.Purchase_Rate) AS Amount,
        sd.Shop_Donor_Name,si.Remarks,si.Purchased_Donation,si.Bill_No
        FROM Stock_Issue si JOIN Grocery_Items gi ON si.Grocery_Code=gi.Grocery_Code
        LEFT JOIN Shops_Donors sd ON si.Shop_Donor_ID=sd.Shop_Donor_ID
        WHERE {' AND '.join(wheres)} ORDER BY si.Rec DESC""", tuple(args))
    return jsonify(logs)

@app.route('/api/godown-stock', methods=['POST'])
def add_godown_stock():
    if not chk('head','godown'): return jsonify({'error':'Unauthorized'}), 403
    d = request.json or {}
    code, donor_id, quantity = d.get('Grocery_Code'), d.get('Shop_Donor_ID'), d.get('Quantity')
    if not code or not donor_id or not quantity: return jsonify({'error':'Fill all required fields'}), 400
    try:
        qty = float(quantity); rate = float(d.get('Purchase_Rate', 0.0))
        if qty <= 0: raise ValueError
    except ValueError: return jsonify({'error':'Quantity must be a positive number'}), 400
    date_str = d.get('Date') or datetime.now().strftime('%Y-%m-%d')
    try:
        db_query("INSERT INTO Stock_Issue (Year1,Date1,Grocery_Code,Shop_Donor_ID,Purchase_Rate,Purchase_Amount,Stock,Issue,Remarks,Purchased_Donation,Bill_No,Bill_Date,DateStamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (datetime.now().year, date_str, code, donor_id, rate, qty*rate, qty, 0.0, d.get('Remarks',''), d.get('Purchased_Donation','Donation'), d.get('Bill_No',''), d.get('Bill_Date',''), datetime.now().strftime('%Y-%m-%d %H:%M:%S')), fetch=False)
        db_query("UPDATE Grocery_Items SET Tot_Stock=Tot_Stock+%s WHERE Grocery_Code=%s", (qty, code), fetch=False)
        log_audit('Inward', 'Add', code, '', f'{qty}')
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500


# --- INDENTS ---

@app.route('/api/indents', methods=['GET'])
def get_indents():
    hid = request.args.get('hostel_id'); sf = request.args.get('status','')
    df = request.args.get('from',''); dt = request.args.get('to','')
    wheres = []; args = []
    if hid: wheres.append("ind.Inst_ID=%s"); args.append(hid)
    if sf: wheres.append("ind.Sanctioned=%s"); args.append(sf)
    if df: wheres.append("ind.Indent_Date>=%s"); args.append(df)
    if dt: wheres.append("ind.Indent_Date<=%s"); args.append(dt)
    where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
    logs = db_query(f"""SELECT ind.Rec,ind.Indent_Date,ind.Grocery_Code,
        gi.Grocery_Items_Kan,gi.Grocery_Items_Eng,gi.Qtl_Kg_Ltr,
        ind.Quantity,ind.Sanctioned_Quantity,ind.Sanctioned,ind.Sanctioned_on,
        ind.Indent_no,ind.Remarks,inst.Institution,ind.Inst_ID
        FROM Indents ind JOIN Grocery_Items gi ON ind.Grocery_Code=gi.Grocery_Code
        JOIN Institutions inst ON ind.Inst_ID=inst.Inst_ID
        {where_sql} ORDER BY ind.Rec DESC""", tuple(args))
    return jsonify(logs)

@app.route('/api/indents', methods=['POST'])
def create_indent():
    if not chk('head','hostel','godown'): return jsonify({'error':'Unauthorized'}), 403
    d = request.json or {}
    inst_id = d.get('Inst_ID') or session.get('inst_id')
    code, quantity = d.get('Grocery_Code'), d.get('Quantity')
    if not inst_id or not code or not quantity: return jsonify({'error':'Fill all required fields'}), 400
    try:
        qty = float(quantity)
        if qty <= 0: raise ValueError
    except ValueError: return jsonify({'error':'Quantity must be positive'}), 400
    indent_no = f"IND-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    try:
        db_query("INSERT INTO Indents (Year1,Indent_Date,Grocery_Code,Inst_ID,Quantity,Indent_no,Sanctioned,Remarks,DateStamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (datetime.now().year, datetime.now().strftime('%Y-%m-%d'), code, inst_id, qty, indent_no, 'Pending', d.get('Remarks',''), datetime.now().strftime('%Y-%m-%d')), fetch=False)
        log_audit('Indents', 'Create', indent_no, '', f'{qty} of {code}')
        return jsonify({'success': True, 'indent_no': indent_no})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/indents/<int:indent_rec>/approve', methods=['POST'])
def approve_indent(indent_rec):
    if not chk('head','godown'): return jsonify({'error':'Unauthorized'}), 403
    d = request.json or {}
    rows = db_query("SELECT * FROM Indents WHERE Rec=%s", (indent_rec,))
    if not rows: return jsonify({'error':'Indent not found'}), 404
    indent = rows[0]
    if indent['Sanctioned'] != 'Pending': return jsonify({'error':'Already processed'}), 400
    sq = float(d.get('Sanctioned_Quantity') or indent['Quantity'])
    if sq <= 0: return jsonify({'error':'Invalid quantity'}), 400
    code = indent['Grocery_Code']
    item_rows = db_query("SELECT Tot_Stock,Std_Rate FROM Grocery_Items WHERE Grocery_Code=%s", (code,))
    if not item_rows: return jsonify({'error':'Item not found'}), 404
    item = item_rows[0]
    if (item['Tot_Stock'] or 0) < sq: return jsonify({'error':f'Insufficient stock. Available: {item["Tot_Stock"]}'}), 400
    try:
        db_query("UPDATE Indents SET Sanctioned_Quantity=%s,Sanctioned='Sent',Sanctioned_on=%s WHERE Rec=%s",
            (sq, datetime.now().strftime('%Y-%m-%d'), indent_rec), fetch=False)
        rate = item['Std_Rate'] or 0.0
        db_query("INSERT INTO Stock_Issue (Year1,Date1,Grocery_Code,Issue_Inst_ID,Issue,Issue_Amount,Remarks,Purchased_Donation,DateStamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (datetime.now().year, datetime.now().strftime('%Y-%m-%d'), code, indent['Inst_ID'], sq, sq*rate, f"Indent {indent['Indent_no']}", 'Issue', datetime.now().strftime('%Y-%m-%d')), fetch=False)
        db_query("UPDATE Grocery_Items SET Tot_Stock=Tot_Stock-%s,Tot_Issue=Tot_Issue+%s WHERE Grocery_Code=%s", (sq,sq,code), fetch=False)
        log_audit('Indents', 'Approve', indent['Indent_no'], indent['Quantity'], sq)
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/indents/<int:indent_rec>/reject', methods=['POST'])
def reject_indent(indent_rec):
    if not chk('head','godown'): return jsonify({'error':'Unauthorized'}), 403
    d = request.json or {}
    rows = db_query("SELECT * FROM Indents WHERE Rec=%s", (indent_rec,))
    if not rows: return jsonify({'error':'Indent not found'}), 404
    if rows[0]['Sanctioned'] != 'Pending': return jsonify({'error':'Already processed'}), 400
    reason = d.get('Reason', 'Rejected')
    try:
        db_query("UPDATE Indents SET Sanctioned='Rejected',Sanctioned_on=%s,Remarks=%s WHERE Rec=%s",
            (datetime.now().strftime('%Y-%m-%d'), reason, indent_rec), fetch=False)
        log_audit('Indents', 'Reject', indent_rec, '', reason)
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/indents/<int:indent_rec>/acknowledge', methods=['POST'])
def acknowledge_indent(indent_rec):
    if not chk('head','hostel','godown'): return jsonify({'error':'Unauthorized'}), 403
    rows = db_query("SELECT * FROM Indents WHERE Rec=%s", (indent_rec,))
    if not rows: return jsonify({'error':'Not found'}), 404
    indent = rows[0]
    if indent['Sanctioned'] == 'Received': return jsonify({'error':'Already acknowledged'}), 400
    col = INST_ID_TO_COLUMN.get(int(indent['Inst_ID']))
    if not col: return jsonify({'error':'Unmapped institution'}), 400
    try:
        db_query("UPDATE Indents SET Sanctioned='Received',Sanctioned_on=%s WHERE Rec=%s",
            (datetime.now().strftime('%Y-%m-%d'), indent_rec), fetch=False)
        db_query(f"UPDATE Grocery_Items SET {col}={col}+%s WHERE Grocery_Code=%s",
            (indent['Sanctioned_Quantity'], indent['Grocery_Code']), fetch=False)
        log_audit('Indents', 'Acknowledge', indent['Indent_no'], '', indent['Sanctioned_Quantity'])
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500


# --- HOSTEL STOCK ---

@app.route('/api/hostel-stock/<int:inst_id>', methods=['GET'])
def get_hostel_stock(inst_id):
    col = INST_ID_TO_COLUMN.get(inst_id)
    if not col: return jsonify([])
    return jsonify(db_query(f"SELECT Grocery_Code,Grocery_Items_Kan,Grocery_Items_Eng,Grocery_Category,Qtl_Kg_Ltr,{col} AS CurrentBalance,Std_Rate FROM Grocery_Items WHERE {col}>=0 ORDER BY Grocery_Category,Grocery_Code"))


# --- DAILY USAGE ---

@app.route('/api/daily-usage', methods=['POST'])
def add_daily_usage():
    if not chk('head','hostel','godown'): return jsonify({'error':'Unauthorized'}), 403
    d = request.json or {}
    inst_id = d.get('Inst_ID') or session.get('inst_id')
    code, quantity = d.get('Grocery_Code'), d.get('Quantity')
    if not inst_id or not code or not quantity: return jsonify({'error':'Fill all required fields'}), 400
    try:
        qty = float(quantity)
        if qty <= 0: raise ValueError
    except ValueError: return jsonify({'error':'Quantity must be positive'}), 400
    col = INST_ID_TO_COLUMN.get(int(inst_id))
    if not col: return jsonify({'error':'Invalid hostel'}), 400
    rows = db_query(f"SELECT {col},Std_Rate FROM Grocery_Items WHERE Grocery_Code=%s", (code,))
    if not rows: return jsonify({'error':'Item not found'}), 404
    item = rows[0]
    if (item[col] or 0) < qty: return jsonify({'error':f'Insufficient. Available: {item[col]}'}), 400
    date_str = d.get('Date') or datetime.now().strftime('%Y-%m-%d')
    try:
        db_query(f"UPDATE Grocery_Items SET {col}={col}-%s WHERE Grocery_Code=%s", (qty,code), fetch=False)
        rate = item['Std_Rate'] or 0.0
        db_query("INSERT INTO Stock_Issue (Year1,Date1,Grocery_Code,Issue_Inst_ID,Issue,Issue_Amount,Remarks,Purchased_Donation,DateStamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (datetime.now().year, date_str, code, inst_id, qty, qty*rate, d.get('Remarks','Consumption'), 'Consumption', datetime.now().strftime('%Y-%m-%d')), fetch=False)
        log_audit('Consumption', 'Add', code, '', f'{qty} by inst {inst_id}')
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/daily-usage/<int:inst_id>', methods=['GET'])
def get_daily_usage_logs(inst_id):
    df = request.args.get('from',''); dt = request.args.get('to','')
    extra = ""; args = [inst_id]
    if df: extra += " AND si.Date1>=%s"; args.append(df)
    if dt: extra += " AND si.Date1<=%s"; args.append(dt)
    return jsonify(db_query(f"""SELECT si.Rec,si.Date1,si.Grocery_Code,gi.Grocery_Items_Kan,gi.Grocery_Items_Eng,
        gi.Qtl_Kg_Ltr,si.Issue AS QuantityUsed,si.Issue_Amount,si.Remarks
        FROM Stock_Issue si JOIN Grocery_Items gi ON si.Grocery_Code=gi.Grocery_Code
        WHERE si.Issue_Inst_ID=%s AND si.Purchased_Donation='Consumption' {extra}
        ORDER BY si.Rec DESC""", tuple(args)))


# --- LOW STOCK ALERTS ---

@app.route('/api/low-stock-alerts', methods=['GET'])
def get_low_stock_alerts():
    alerts = []
    for inst_id, col in INST_ID_TO_COLUMN.items():
        inst_rows = db_query("SELECT Institution FROM Institutions WHERE Inst_ID=%s", (inst_id,))
        if not inst_rows: continue
        inst_name = inst_rows[0]['Institution']
        for item in db_query(f"SELECT Grocery_Code,Grocery_Items_Kan,Qtl_Kg_Ltr,{col} AS CurrentBalance FROM Grocery_Items WHERE {col}<10.0 AND {col}>=0"):
            alerts.append({'Inst_ID':inst_id,'Institution':inst_name,'Grocery_Code':item['Grocery_Code'],'Grocery_Items_Kan':item['Grocery_Items_Kan'],'Qtl_Kg_Ltr':item['Qtl_Kg_Ltr'],'CurrentBalance':item['CurrentBalance']})
    return jsonify(alerts)


# --- VEGETABLES ---

@app.route('/api/vegetables', methods=['GET'])
def get_vegetables():
    iid = request.args.get('inst_id'); df = request.args.get('from',''); dt = request.args.get('to','')
    wheres = []; args = []
    if iid: wheres.append("v.Inst_ID=%s"); args.append(iid)
    if df: wheres.append("v.Purchase_On>=%s"); args.append(df)
    if dt: wheres.append("v.Purchase_On<=%s"); args.append(dt)
    where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
    return jsonify(db_query(f"SELECT v.*,i.Institution FROM Vegetable v JOIN Institutions i ON v.Inst_ID=i.Inst_ID {where_sql} ORDER BY v.Rec DESC", tuple(args)))

@app.route('/api/vegetables', methods=['POST'])
def add_vegetable():
    if not chk('head','godown','hostel'): return jsonify({'error':'Unauthorized'}), 403
    d = request.json or {}
    try:
        db_query("INSERT INTO Vegetable (Inst_ID,Year1,Purchase_On,V_Code,Quantity,Bill_Date,Bill_No,Rate,Remarks,Issue_Place,Purchased_Donation) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (d.get('Inst_ID') or session.get('inst_id'), datetime.now().year, d.get('Purchase_On'), d.get('V_Code'), d.get('Quantity',0.0), d.get('Bill_Date'), d.get('Bill_No'), d.get('Rate',0.0), d.get('Remarks'), d.get('Issue_Place'), d.get('Purchased_Donation','Purchase')), fetch=False)
        log_audit('Vegetables','Add',d.get('V_Code',''),'',d.get('Quantity',''))
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500


# --- BILLS ---

@app.route('/api/bills', methods=['GET'])
def get_bills():
    df = request.args.get('from',''); dt = request.args.get('to',''); dn = request.args.get('donor','')
    wheres = []; args = []
    if df: wheres.append("b.Bill_Date>=%s"); args.append(df)
    if dt: wheres.append("b.Bill_Date<=%s"); args.append(dt)
    if dn: wheres.append("b.Shop_Donor_ID=%s"); args.append(dn)
    where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
    return jsonify(db_query(f"SELECT b.*,sd.Shop_Donor_Name,sd.Place FROM Bills b LEFT JOIN Shops_Donors sd ON b.Shop_Donor_ID=sd.Shop_Donor_ID {where_sql} ORDER BY b.Rec DESC", tuple(args)))

@app.route('/api/bills', methods=['POST'])
def add_bill():
    if not chk('head','accounts','godown'): return jsonify({'error':'Unauthorized'}), 403
    d = request.json or {}
    try:
        db_query("INSERT INTO Bills (Year1,Shop_Donor_ID,Bill_Date,Bill_No,Bill_Amount,Paid_By,Ch_Date,Ch_No,Ch_Amount,Remarks,DateAdded) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (datetime.now().year, d.get('Shop_Donor_ID'), d.get('Bill_Date'), d.get('Bill_No'), d.get('Bill_Amount',0.0), d.get('Paid_By'), d.get('Ch_Date'), d.get('Ch_No'), d.get('Ch_Amount',0.0), d.get('Remarks'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')), fetch=False)
        log_audit('Bills','Add',d.get('Bill_No',''),'',d.get('Bill_Amount',''))
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/bills/<int:rec>', methods=['DELETE'])
def delete_bill(rec):
    if not chk('head','accounts'): return jsonify({'error':'Unauthorized'}), 403
    try:
        db_query("DELETE FROM Bills WHERE Rec=%s", (rec,), fetch=False)
        log_audit('Bills','Delete',rec)
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500


# --- REPORTS ---

@app.route('/api/reports/stock', methods=['GET'])
def report_stock():
    cat = request.args.get('category','')
    args = []; where = ""
    if cat: where = "WHERE Grocery_Category=%s"; args.append(cat)
    return jsonify(db_query(f"SELECT Grocery_Code,Grocery_Items_Kan,Grocery_Items_Eng,Grocery_Category,Qtl_Kg_Ltr,Tot_Stock,Tot_Issue,Std_Rate,(Tot_Stock*Std_Rate) AS StockValue FROM Grocery_Items {where} ORDER BY Grocery_Category,Grocery_Code", tuple(args)))

@app.route('/api/reports/purchases', methods=['GET'])
def report_purchases():
    df = request.args.get('from',''); dt = request.args.get('to',''); dn = request.args.get('donor',''); tp = request.args.get('type','')
    wheres = ["si.Stock>0"]; args = []
    if df: wheres.append("si.Date1>=%s"); args.append(df)
    if dt: wheres.append("si.Date1<=%s"); args.append(dt)
    if dn: wheres.append("si.Shop_Donor_ID=%s"); args.append(dn)
    if tp: wheres.append("si.Purchased_Donation=%s"); args.append(tp)
    return jsonify(db_query(f"""SELECT si.Date1,si.Grocery_Code,gi.Grocery_Items_Kan,gi.Grocery_Items_Eng,
        gi.Qtl_Kg_Ltr,si.Stock AS Quantity,si.Purchase_Rate,(si.Stock*si.Purchase_Rate) AS Amount,
        sd.Shop_Donor_Name,si.Bill_No,si.Purchased_Donation,si.Remarks
        FROM Stock_Issue si JOIN Grocery_Items gi ON si.Grocery_Code=gi.Grocery_Code
        LEFT JOIN Shops_Donors sd ON si.Shop_Donor_ID=sd.Shop_Donor_ID
        WHERE {' AND '.join(wheres)} ORDER BY si.Date1 DESC,si.Rec DESC""", tuple(args)))

@app.route('/api/reports/indents', methods=['GET'])
def report_indents():
    df = request.args.get('from',''); dt = request.args.get('to',''); sf = request.args.get('status',''); iid = request.args.get('inst_id','')
    wheres = []; args = []
    if df: wheres.append("ind.Indent_Date>=%s"); args.append(df)
    if dt: wheres.append("ind.Indent_Date<=%s"); args.append(dt)
    if sf: wheres.append("ind.Sanctioned=%s"); args.append(sf)
    if iid: wheres.append("ind.Inst_ID=%s"); args.append(iid)
    where_sql = ("WHERE " + " AND ".join(wheres)) if wheres else ""
    return jsonify(db_query(f"""SELECT ind.Indent_Date,ind.Indent_no,inst.Institution,
        gi.Grocery_Items_Kan,gi.Grocery_Items_Eng,gi.Qtl_Kg_Ltr,
        ind.Quantity,ind.Sanctioned_Quantity,ind.Sanctioned,ind.Sanctioned_on,ind.Remarks
        FROM Indents ind JOIN Grocery_Items gi ON ind.Grocery_Code=gi.Grocery_Code
        JOIN Institutions inst ON ind.Inst_ID=inst.Inst_ID {where_sql}
        ORDER BY ind.Indent_Date DESC,ind.Rec DESC""", tuple(args)))

@app.route('/api/reports/consumption', methods=['GET'])
def report_consumption():
    df = request.args.get('from',''); dt = request.args.get('to',''); iid = request.args.get('inst_id','')
    wheres = ["si.Purchased_Donation='Consumption'"]; args = []
    if df: wheres.append("si.Date1>=%s"); args.append(df)
    if dt: wheres.append("si.Date1<=%s"); args.append(dt)
    if iid: wheres.append("si.Issue_Inst_ID=%s"); args.append(iid)
    return jsonify(db_query(f"""SELECT si.Date1,inst.Institution,gi.Grocery_Items_Kan,gi.Grocery_Items_Eng,
        gi.Qtl_Kg_Ltr,gi.Grocery_Category,si.Issue AS QuantityUsed,si.Issue_Amount,si.Remarks
        FROM Stock_Issue si JOIN Grocery_Items gi ON si.Grocery_Code=gi.Grocery_Code
        JOIN Institutions inst ON si.Issue_Inst_ID=inst.Inst_ID
        WHERE {' AND '.join(wheres)} ORDER BY si.Date1 DESC,si.Rec DESC""", tuple(args)))

@app.route('/api/reports/donations', methods=['GET'])
def report_donations():
    df = request.args.get('from',''); dt = request.args.get('to',''); dn = request.args.get('donor','')
    wheres = ["si.Purchased_Donation='Donation'"]; args = []
    if df: wheres.append("si.Date1>=%s"); args.append(df)
    if dt: wheres.append("si.Date1<=%s"); args.append(dt)
    if dn: wheres.append("si.Shop_Donor_ID=%s"); args.append(dn)
    return jsonify(db_query(f"""SELECT si.Date1,sd.Shop_Donor_Name,sd.Place,
        gi.Grocery_Items_Kan,gi.Grocery_Items_Eng,gi.Qtl_Kg_Ltr,si.Stock AS Quantity,si.Remarks
        FROM Stock_Issue si JOIN Grocery_Items gi ON si.Grocery_Code=gi.Grocery_Code
        LEFT JOIN Shops_Donors sd ON si.Shop_Donor_ID=sd.Shop_Donor_ID
        WHERE {' AND '.join(wheres)} ORDER BY si.Date1 DESC""", tuple(args)))


# --- AUDIT LOGS ---

@app.route('/api/audit-logs', methods=['GET'])
def get_audit_logs():
    if not chk('head'): return jsonify({'error':'Unauthorized'}), 403
    return jsonify(db_query("SELECT * FROM Audit_Logs ORDER BY Rec DESC LIMIT 500"))


# --- USERS ---

@app.route('/api/users', methods=['GET'])
def get_users():
    if not chk('head'): return jsonify({'error':'Unauthorized'}), 403
    return jsonify(db_query("SELECT username,role,inst_id,name FROM Users ORDER BY role,username"))

@app.route('/api/users', methods=['POST'])
def create_user():
    if not chk('head'): return jsonify({'error':'Unauthorized'}), 403
    d = request.json or {}
    un = d.get('username','').strip().lower(); pw = d.get('password','').strip()
    role = d.get('role','').strip(); name = d.get('name','').strip()
    if not un or not pw or not role or not name: return jsonify({'error':'All fields required'}), 400
    try:
        if db_query("SELECT username FROM Users WHERE username=%s", (un,)): return jsonify({'error':'Username exists'}), 400
        db_query("INSERT INTO Users (username,password,role,inst_id,name) VALUES (%s,%s,%s,%s,%s)",
            (un, pw, role, d.get('inst_id'), name), fetch=False)
        log_audit('Users','Create',un,'',role)
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/users/<username>', methods=['PUT'])
def edit_user(username):
    if not chk('head'): return jsonify({'error':'Unauthorized'}), 403
    d = request.json or {}
    name = d.get('name','').strip(); role = d.get('role','').strip()
    pw = d.get('password','').strip(); inst_id = d.get('inst_id')
    try:
        if pw:
            db_query("UPDATE Users SET name=%s,role=%s,inst_id=%s,password=%s WHERE username=%s", (name,role,inst_id,pw,username), fetch=False)
        else:
            db_query("UPDATE Users SET name=%s,role=%s,inst_id=%s WHERE username=%s", (name,role,inst_id,username), fetch=False)
        log_audit('Users','Edit',username,'',role)
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/api/users/<username>', methods=['DELETE'])
def delete_user(username):
    if not chk('head'): return jsonify({'error':'Unauthorized'}), 403
    if username == session.get('username'): return jsonify({'error':'Cannot delete own account'}), 400
    try:
        db_query("DELETE FROM Users WHERE username=%s", (username,), fetch=False)
        log_audit('Users','Delete',username)
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500


# --- DB INIT ---

def init_db():
    try:
        db_query("CREATE TABLE IF NOT EXISTS Users (username VARCHAR(50) PRIMARY KEY, password VARCHAR(100) NOT NULL, role VARCHAR(20) NOT NULL, inst_id INT, name VARCHAR(100) NOT NULL)", fetch=False)
        db_query("CREATE TABLE IF NOT EXISTS Audit_Logs (Rec INTEGER PRIMARY KEY AUTOINCREMENT, Timestamp TEXT NOT NULL, Username TEXT NOT NULL, Module TEXT NOT NULL, Action TEXT NOT NULL, Target_ID TEXT, Old_Value TEXT, New_Value TEXT)", fetch=False)
        existing = db_query("SELECT COUNT(*) as cnt FROM Users")
        count = existing[0].get('cnt', 0) if existing else 0
        if count == 0:
            for un, info in USERS.items():
                db_query("INSERT INTO Users (username,password,role,inst_id,name) VALUES (%s,%s,%s,%s,%s)",
                    (un, info['password'], info['role'], info['inst_id'], info['name']), fetch=False)
            print("Default users seeded.")
    except Exception as e:
        print(f"DB init error: {e}")


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
