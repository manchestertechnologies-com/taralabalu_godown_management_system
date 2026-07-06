import os
import sqlite3
import urllib.parse
import psycopg2

# Supabase Connection String (Default)
SUPABASE_URL = "postgresql://postgres:Bery8792480218@db.rsvkrseaxewamlipnuku.supabase.co:5432/postgres"
SUPABASE_URL_ALT = "postgresql://postgres:[Bery8792480218]@db.rsvkrseaxewamlipnuku.supabase.co:5432/postgres"

def get_connection():
    # Try connecting to PostgreSQL / Supabase
    connection_strings = [
        os.environ.get('DATABASE_URL', SUPABASE_URL),
        SUPABASE_URL_ALT
    ]
    
    for conn_str in connection_strings:
        # Clean up any potential brackets in connection URL
        cleaned_str = conn_str.replace(":[Bery8792480218]@", ":Bery8792480218@")
        try:
            print(f"Attempting to connect to PostgreSQL (Supabase)...")
            # Parse URL into parts to connect via parameters (handles odd characters safely)
            result = urllib.parse.urlparse(cleaned_str)
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
            print("Successfully connected to PostgreSQL (Supabase).")
            return conn, "postgresql"
        except Exception as e:
            print(f"PostgreSQL connection failed with URL: {cleaned_str.split('@')[-1]}. Error: {e}")
            
    # Fallback to local SQLite using absolute path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'database.db')
    print(f"Falling back to local SQLite database '{db_path}'...")
    conn = sqlite3.connect(db_path)
    return conn, "sqlite"


def execute_ddl(cursor, db_type, query_pg, query_sqlite):
    query = query_pg if db_type == "postgresql" else query_sqlite
    cursor.execute(query)

def init_db():
    conn, db_type = get_connection()
    cursor = conn.cursor()
    
    # 1. Institutions Table
    if db_type == "postgresql":
        cursor.execute("DROP TABLE IF EXISTS Institutions CASCADE;")
        cursor.execute("""
            CREATE TABLE Institutions (
                Inst_ID SERIAL PRIMARY KEY,
                Institution VARCHAR(100) UNIQUE NOT NULL
            );
        """)
    else:
        cursor.execute("DROP TABLE IF EXISTS Institutions;")
        cursor.execute("""
            CREATE TABLE Institutions (
                Inst_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                Institution TEXT UNIQUE NOT NULL
            );
        """)

    # 2. Shops_Donors Table
    if db_type == "postgresql":
        cursor.execute("DROP TABLE IF EXISTS Shops_Donors CASCADE;")
        cursor.execute("""
            CREATE TABLE Shops_Donors (
                Rec SERIAL PRIMARY KEY,
                Year1 VARCHAR(10),
                Shop_Donor_ID INTEGER UNIQUE NOT NULL,
                Shop_Donor_Name VARCHAR(200) NOT NULL,
                Place_ID INTEGER,
                Place VARCHAR(100),
                Place_Kan VARCHAR(100),
                Taluk VARCHAR(100),
                Taluk_Kan VARCHAR(100),
                Dist VARCHAR(100),
                Dist_Kan VARCHAR(100),
                Pin VARCHAR(20),
                State VARCHAR(100),
                Country VARCHAR(100),
                Mobile VARCHAR(20),
                Remarks TEXT,
                DateStamp VARCHAR(50)
            );
        """)
    else:
        cursor.execute("DROP TABLE IF EXISTS Shops_Donors;")
        cursor.execute("""
            CREATE TABLE Shops_Donors (
                Rec INTEGER PRIMARY KEY AUTOINCREMENT,
                Year1 TEXT,
                Shop_Donor_ID INTEGER UNIQUE NOT NULL,
                Shop_Donor_Name TEXT NOT NULL,
                Place_ID INTEGER,
                Place TEXT,
                Place_Kan TEXT,
                Taluk TEXT,
                Taluk_Kan TEXT,
                Dist TEXT,
                Dist_Kan TEXT,
                Pin TEXT,
                State TEXT,
                Country TEXT,
                Mobile TEXT,
                Remarks TEXT,
                DateStamp TEXT
            );
        """)

    # 3. Grocery_Items Table
    if db_type == "postgresql":
        cursor.execute("DROP TABLE IF EXISTS Grocery_Items CASCADE;")
        cursor.execute("""
            CREATE TABLE Grocery_Items (
                Rec SERIAL PRIMARY KEY,
                Grocery_Code INTEGER UNIQUE NOT NULL,
                Grocery_Items_Kan VARCHAR(200) NOT NULL,
                Grocery_Items_Eng VARCHAR(200),
                Grocery_Category VARCHAR(100),
                Category_Code VARCHAR(20),
                Std_Rate REAL DEFAULT 0.0,
                Qtl_Kg_Ltr VARCHAR(20),
                Shraddanjali_Qty REAL DEFAULT 0.0,
                Hunnime_Qty REAL DEFAULT 0.0,
                Boys_Hostel_Qty REAL DEFAULT 0.0,
                Girls_Hostel_Qty REAL DEFAULT 0.0,
                Math_Qty REAL DEFAULT 0.0,
                Shantivan_Qty_a REAL DEFAULT 0.0,
                AO_Office_Qty REAL DEFAULT 0.0,
                Tot_Quantity REAL DEFAULT 0.0,
                Opening_Stock REAL DEFAULT 0.0,
                Closing_Stock REAL DEFAULT 0.0,
                Tot_Stock REAL DEFAULT 0.0,
                Tot_Issue REAL DEFAULT 0.0,
                Stock_Amt REAL DEFAULT 0.0,
                Total_Budget REAL DEFAULT 0.0,
                Remarks TEXT,
                DateStamp VARCHAR(50)
            );
        """)
    else:
        cursor.execute("DROP TABLE IF EXISTS Grocery_Items;")
        cursor.execute("""
            CREATE TABLE Grocery_Items (
                Rec INTEGER PRIMARY KEY AUTOINCREMENT,
                Grocery_Code INTEGER UNIQUE NOT NULL,
                Grocery_Items_Kan TEXT NOT NULL,
                Grocery_Items_Eng TEXT,
                Grocery_Category TEXT,
                Category_Code TEXT,
                Std_Rate REAL DEFAULT 0.0,
                Qtl_Kg_Ltr TEXT,
                Shraddanjali_Qty REAL DEFAULT 0.0,
                Hunnime_Qty REAL DEFAULT 0.0,
                Boys_Hostel_Qty REAL DEFAULT 0.0,
                Girls_Hostel_Qty REAL DEFAULT 0.0,
                Math_Qty REAL DEFAULT 0.0,
                Shantivan_Qty_a REAL DEFAULT 0.0,
                AO_Office_Qty REAL DEFAULT 0.0,
                Tot_Quantity REAL DEFAULT 0.0,
                Opening_Stock REAL DEFAULT 0.0,
                Closing_Stock REAL DEFAULT 0.0,
                Tot_Stock REAL DEFAULT 0.0,
                Tot_Issue REAL DEFAULT 0.0,
                Stock_Amt REAL DEFAULT 0.0,
                Total_Budget REAL DEFAULT 0.0,
                Remarks TEXT,
                DateStamp TEXT
            );
        """)

    # 4. Stock_Issue Table
    if db_type == "postgresql":
        cursor.execute("DROP TABLE IF EXISTS Stock_Issue CASCADE;")
        cursor.execute("""
            CREATE TABLE Stock_Issue (
                Rec SERIAL PRIMARY KEY,
                Year1 VARCHAR(10),
                Date1 VARCHAR(20),
                Grocery_Code INTEGER REFERENCES Grocery_Items(Grocery_Code),
                Shop_Donor_ID INTEGER,
                Book_No VARCHAR(50),
                Receipt_No VARCHAR(50),
                Receipt_Date VARCHAR(20),
                Bill_Date VARCHAR(20),
                Bill_No VARCHAR(50),
                Purchase_Rate REAL DEFAULT 0.0,
                Purchase_Amount REAL DEFAULT 0.0,
                Paid VARCHAR(20),
                Stock REAL DEFAULT 0.0,
                Issue_Inst_ID INTEGER REFERENCES Institutions(Inst_ID),
                Issue REAL DEFAULT 0.0,
                Issue_Amount REAL DEFAULT 0.0,
                Received_By VARCHAR(100),
                DateStamp VARCHAR(50),
                Remarks TEXT,
                Purchased_Donation VARCHAR(20)
            );
        """)
    else:
        cursor.execute("DROP TABLE IF EXISTS Stock_Issue;")
        cursor.execute("""
            CREATE TABLE Stock_Issue (
                Rec INTEGER PRIMARY KEY AUTOINCREMENT,
                Year1 TEXT,
                Date1 TEXT,
                Grocery_Code INTEGER,
                Shop_Donor_ID INTEGER,
                Book_No TEXT,
                Receipt_No TEXT,
                Receipt_Date TEXT,
                Bill_Date TEXT,
                Bill_No TEXT,
                Purchase_Rate REAL DEFAULT 0.0,
                Purchase_Amount REAL DEFAULT 0.0,
                Paid TEXT,
                Stock REAL DEFAULT 0.0,
                Issue_Inst_ID INTEGER,
                Issue REAL DEFAULT 0.0,
                Issue_Amount REAL DEFAULT 0.0,
                Received_By TEXT,
                DateStamp TEXT,
                Remarks TEXT,
                Purchased_Donation TEXT,
                FOREIGN KEY(Grocery_Code) REFERENCES Grocery_Items(Grocery_Code),
                FOREIGN KEY(Issue_Inst_ID) REFERENCES Institutions(Inst_ID)
            );
        """)

    # 5. Bills Table
    if db_type == "postgresql":
        cursor.execute("DROP TABLE IF EXISTS Bills CASCADE;")
        cursor.execute("""
            CREATE TABLE Bills (
                Rec SERIAL PRIMARY KEY,
                Year1 VARCHAR(10),
                Shop_Donor_ID INTEGER,
                Bill_Date VARCHAR(20),
                Bill_No VARCHAR(50),
                Bill_Amount REAL DEFAULT 0.0,
                Paid_By VARCHAR(100),
                Ch_Date VARCHAR(20),
                Ch_No VARCHAR(50),
                Ch_Amount REAL DEFAULT 0.0,
                Remarks TEXT,
                DateAdded VARCHAR(50)
            );
        """)
    else:
        cursor.execute("DROP TABLE IF EXISTS Bills;")
        cursor.execute("""
            CREATE TABLE Bills (
                Rec INTEGER PRIMARY KEY AUTOINCREMENT,
                Year1 TEXT,
                Shop_Donor_ID INTEGER,
                Bill_Date TEXT,
                Bill_No TEXT,
                Bill_Amount REAL DEFAULT 0.0,
                Paid_By TEXT,
                Ch_Date TEXT,
                Ch_No TEXT,
                Ch_Amount REAL DEFAULT 0.0,
                Remarks TEXT,
                DateAdded TEXT
            );
        """)

    # 6. Vegetable Table
    if db_type == "postgresql":
        cursor.execute("DROP TABLE IF EXISTS Vegetable CASCADE;")
        cursor.execute("""
            CREATE TABLE Vegetable (
                Rec SERIAL PRIMARY KEY,
                Inst_ID INTEGER REFERENCES Institutions(Inst_ID),
                Year1 VARCHAR(10),
                Purchase_On VARCHAR(20),
                V_Code VARCHAR(20),
                Quantity REAL DEFAULT 0.0,
                Bill_Date VARCHAR(20),
                Bill_No VARCHAR(50),
                Rate REAL DEFAULT 0.0,
                Remarks TEXT,
                Issue_Place VARCHAR(100),
                Purchased_Donation VARCHAR(20)
            );
        """)
    else:
        cursor.execute("DROP TABLE IF EXISTS Vegetable;")
        cursor.execute("""
            CREATE TABLE Vegetable (
                Rec INTEGER PRIMARY KEY AUTOINCREMENT,
                Inst_ID INTEGER,
                Year1 TEXT,
                Purchase_On TEXT,
                V_Code TEXT,
                Quantity REAL DEFAULT 0.0,
                Bill_Date TEXT,
                Bill_No TEXT,
                Rate REAL DEFAULT 0.0,
                Remarks TEXT,
                Issue_Place TEXT,
                Purchased_Donation TEXT,
                FOREIGN KEY(Inst_ID) REFERENCES Institutions(Inst_ID)
            );
        """)

    # 7. Indents Table
    if db_type == "postgresql":
        cursor.execute("DROP TABLE IF EXISTS Indents CASCADE;")
        cursor.execute("""
            CREATE TABLE Indents (
                Rec SERIAL PRIMARY KEY,
                Year1 VARCHAR(10),
                Indent_Date VARCHAR(20),
                Grocery_Code INTEGER REFERENCES Grocery_Items(Grocery_Code),
                Inst_ID INTEGER REFERENCES Institutions(Inst_ID),
                Quantity REAL DEFAULT 0.0,
                Indent_no VARCHAR(50),
                Sanctioned_Quantity REAL DEFAULT 0.0,
                Sanctioned VARCHAR(50) DEFAULT 'Pending', -- 'Pending', 'Sent', 'Received'
                Sanctioned_on VARCHAR(20),
                DateStamp VARCHAR(50),
                Remarks TEXT
            );
        """)
    else:
        cursor.execute("DROP TABLE IF EXISTS Indents;")
        cursor.execute("""
            CREATE TABLE Indents (
                Rec INTEGER PRIMARY KEY AUTOINCREMENT,
                Year1 TEXT,
                Indent_Date TEXT,
                Grocery_Code INTEGER,
                Inst_ID INTEGER,
                Quantity REAL DEFAULT 0.0,
                Indent_no TEXT,
                Sanctioned_Quantity REAL DEFAULT 0.0,
                Sanctioned TEXT DEFAULT 'Pending',
                Sanctioned_on TEXT,
                DateStamp TEXT,
                Remarks TEXT,
                FOREIGN KEY(Grocery_Code) REFERENCES Grocery_Items(Grocery_Code),
                FOREIGN KEY(Inst_ID) REFERENCES Institutions(Inst_ID)
            );
        """)

    # --- SEEDING PRE-FILL DATA ---

    # Institutions Seed
    institutions = [
        ("Boys Hostel",),
        ("Girls Hostel",),
        ("Math",),
        ("Shantivana Bidara",),
        ("Shantivana Gurukula",),
        ("Sirigere BHS",),
        ("Sirigere GHS",),
        ("AO_Office",),
        ("Shraddhajali",)
    ]
    cursor.executemany("INSERT INTO Institutions (Institution) VALUES (%s)" if db_type == "postgresql" else "INSERT INTO Institutions (Institution) VALUES (?)", institutions)

    # Shops / Donors Seed
    donors = [
        ('2026', 2001, 'ಕರ್ನಾಟಕ ಆಹಾರ ಮತ್ತು ನಾಗರಿಕ ಸರಬರಾಜು ನಿಗಮ (KFSN)', 1, 'ಬೆಂಗಳೂರು', 'Bengaluru', 'ಬೆಂಗಳೂರು', 'Bengaluru', 'ಬೆಂಗಳೂರು', 'Bengaluru', '560001', 'Karnataka', 'India', '080-22221111', 'ಸರಕಾರಿ ಕೋಟಾ ಸರಬರಾಜು', '2026-07-06'),
        ('2026', 2002, 'ಶ್ರೀ ತರಳಬಾಳು ಭಕ್ತ ಮಂಡಳಿ', 2, 'ಸಿರಿಗೆರೆ', 'Sirigere', 'ಚಿತ್ರದುರ್ಗ', 'Chitradurga', 'ಚಿತ್ರದುರ್ಗ', 'Chitradurga', '577541', 'Karnataka', 'India', '9876543210', 'ದವಸ ಧಾನ್ಯ ದೇಣಿಗೆ', '2026-07-06'),
        ('2026', 2003, 'ಸ್ಥಳೀಯ ರೈತ ಸಹಕಾರ ಸಂಘ', 3, 'ಸಿರಿಗೆರೆ', 'Sirigere', 'ಚಿತ್ರದುರ್ಗ', 'Chitradurga', 'ಚಿತ್ರದುರ್ಗ', 'Chitradurga', '577541', 'Karnataka', 'India', '9900112233', 'ತರಕಾರಿ ದಾನಿಗಳು', '2026-07-06')
    ]
    cursor.executemany("""
        INSERT INTO Shops_Donors 
        (Year1, Shop_Donor_ID, Shop_Donor_Name, Place_ID, Place, Place_Kan, Taluk, Taluk_Kan, Dist, Dist_Kan, Pin, State, Country, Mobile, Remarks, DateStamp)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """ if db_type == "postgresql" else """
        INSERT INTO Shops_Donors 
        (Year1, Shop_Donor_ID, Shop_Donor_Name, Place_ID, Place, Place_Kan, Taluk, Taluk_Kan, Dist, Dist_Kan, Pin, State, Country, Mobile, Remarks, DateStamp)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, donors)

    # Dynamic CSV scanner for grocery items
    import csv
    csv_loaded = False
    csv_files = [f for f in os.listdir(base_dir) if f.endswith('.csv')]
    
    for f_name in csv_files:
        csv_path = os.path.join(base_dir, f_name)
        try:
            with open(csv_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                # Validate if it looks like a grocery items CSV
                if headers and any(h.lower().replace(" ", "_") in ['grocery_code', 'code', 'grocerycode'] for h in headers):
                    print(f"Detected grocery dataset at '{f_name}'. Parsing and importing...")
                    items = []
                    for row in reader:
                        code = 0
                        for h in headers:
                            if h.lower().replace(" ", "_") in ['grocery_code', 'code', 'grocerycode']:
                                try:
                                    code = int(float(row[h]))
                                except:
                                    pass
                        if not code:
                            continue
                            
                        # Extract Kannada name
                        name_kan = ""
                        for h in headers:
                            if h.lower().replace(" ", "_") in ['grocery_items_kan', 'grocery_items_kannada', 'item_name_kannada', 'kannada_name', 'items_kan']:
                                name_kan = row[h]
                        if not name_kan:
                            for h in headers:
                                if 'name' in h.lower() or 'item' in h.lower():
                                    name_kan = row[h]
                                    break
                                    
                        # Extract English name
                        name_eng = ""
                        for h in headers:
                            if h.lower().replace(" ", "_") in ['grocery_items_eng', 'grocery_items_english', 'item_name_english', 'english_name', 'items_eng']:
                                name_eng = row[h]
                                
                        # Category
                        category = "ಧಾನ್ಯಗಳು"
                        for h in headers:
                            if 'category' in h.lower():
                                category = row[h]
                                
                        # Unit
                        unit = "ಕೆಜಿ (KG)"
                        for h in headers:
                            if h.lower().replace(" ", "_") in ['qtl_kg_ltr', 'unit', 'unit_type']:
                                unit = row[h]
                                
                        # Rate
                        rate = 0.0
                        for h in headers:
                            if h.lower().replace(" ", "_") in ['std_rate', 'rate', 'standard_rate']:
                                try:
                                    rate = float(row[h])
                                except:
                                    pass
                                    
                        # Branch stock parsing
                        boys_qty = 0.0
                        girls_qty = 0.0
                        math_qty = 0.0
                        shantivan_qty = 0.0
                        ao_office_qty = 0.0
                        shraddanjali_qty = 0.0
                        hunnime_qty = 0.0
                        
                        for h in headers:
                            hl = h.lower()
                            if 'boys' in hl:
                                try: boys_qty = float(row[h])
                                except: pass
                            elif 'girls' in hl:
                                try: girls_qty = float(row[h])
                                except: pass
                            elif 'math' in hl:
                                try: math_qty = float(row[h])
                                except: pass
                            elif 'shantivan' in hl:
                                try: shantivan_qty = float(row[h])
                                except: pass
                            elif 'office' in hl or 'ao' in hl:
                                try: ao_office_qty = float(row[h])
                                except: pass
                            elif 'shraddanjali' in hl or 'shraddhajali' in hl:
                                try: shraddanjali_qty = float(row[h])
                                except: pass
                            elif 'hunnime' in hl:
                                try: hunnime_qty = float(row[h])
                                except: pass
                                
                        tot_qty = boys_qty + girls_qty + math_qty + shantivan_qty + ao_office_qty + shraddanjali_qty + hunnime_qty
                        
                        items.append((
                            code, name_kan, name_eng, category, 'C01', rate, unit,
                            shraddanjali_qty, hunnime_qty, boys_qty, girls_qty, math_qty, shantivan_qty, ao_office_qty,
                            tot_qty, tot_qty, tot_qty, tot_qty + 100, 0.0, tot_qty * rate, tot_qty * rate * 1.5, 'Imported from ' + f_name, datetime.now().strftime('%Y-%m-%d')
                        ))
                    
                    if items:
                        # Clear default items and insert new ones
                        cursor.execute("DELETE FROM Grocery_Items;")
                        cursor.executemany("""
                            INSERT INTO Grocery_Items
                            (Grocery_Code, Grocery_Items_Kan, Grocery_Items_Eng, Grocery_Category, Category_Code, Std_Rate, Qtl_Kg_Ltr,
                             Shraddanjali_Qty, Hunnime_Qty, Boys_Hostel_Qty, Girls_Hostel_Qty, Math_Qty, Shantivan_Qty_a, AO_Office_Qty,
                             Tot_Quantity, Opening_Stock, Closing_Stock, Tot_Stock, Tot_Issue, Stock_Amt, Total_Budget, Remarks, DateStamp)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """ if db_type == "postgresql" else """
                            INSERT INTO Grocery_Items
                            (Grocery_Code, Grocery_Items_Kan, Grocery_Items_Eng, Grocery_Category, Category_Code, Std_Rate, Qtl_Kg_Ltr,
                             Shraddanjali_Qty, Hunnime_Qty, Boys_Hostel_Qty, Girls_Hostel_Qty, Math_Qty, Shantivan_Qty_a, AO_Office_Qty,
                             Tot_Quantity, Opening_Stock, Closing_Stock, Tot_Stock, Tot_Issue, Stock_Amt, Total_Budget, Remarks, DateStamp)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        """, items)
                        print(f"Successfully loaded {len(items)} items from CSV file: {f_name}")
                        csv_loaded = True
                        break
        except Exception as e:
            print(f"Error parsing CSV '{f_name}': {e}")

    if not csv_loaded:
        print("No CSV file found or parsing failed. Seeding default dummy items instead.")
        # Seeding default items list
        items = [
            (101, 'ಅಕ್ಕಿ (Rice)', 'Rice', 'ಧಾನ್ಯಗಳು', 'C01', 45.0, 'ಕೆಜಿ (KG)', 200.0, 100.0, 1500.0, 1200.0, 500.0, 300.0, 100.0, 3900.0, 2000.0, 3900.0, 5000.0, 1100.0, 49500.0, 100000.0, 'ದಿನನಿತ್ಯದ ಅಡುಗೆಗೆ', '2026-07-06'),
            (102, 'ಗೋಧಿ ಹಿಟ್ಟು (Wheat Flour)', 'Wheat Flour', 'ಹಿಟ್ಟು', 'C02', 38.0, 'ಕೆಜಿ (KG)', 50.0, 20.0, 4.0, 250.0, 100.0, 150.0, 50.0, 624.0, 100.0, 624.0, 1000.0, 376.0, 23712.0, 50000.0, 'Low Stock Alert triggered for Boys Hostel (4.0 KG)', '2026-07-06'),
            (103, 'ತೊಗರಿ ಬೇಳε (Toor Dal)', 'Toor Dal', 'ಬೇಳೆಕಾಳು', 'C03', 120.0, 'ಕೆಜಿ (KG)', 10.0, 50.0, 120.0, 90.0, 40.0, 5.0, 10.0, 325.0, 500.0, 325.0, 1000.0, 675.0, 39000.0, 80000.0, 'Low Stock Alert triggered for Shantivana (5.0 KG)', '2026-07-06'),
            (104, 'ಸಕ್ಕರೆ (Sugar)', 'Sugar', 'ಸಿಹಿ ವಸ್ತು', 'C04', 40.0, 'ಕೆಜಿ (KG)', 10.0, 30.0, 80.0, 60.0, 30.0, 40.0, 20.0, 270.0, 200.0, 270.0, 500.0, 230.0, 10800.0, 25000.0, '', '2026-07-06'),
            (105, 'ಅಡುಗೆ ಎಣ್ಣೆ (Cooking Oil)', 'Cooking Oil', 'ಎಣ್ಣೆ', 'C05', 110.0, 'ಲೀಟರ್ (Ltr)', 5.0, 10.0, 90.0, 80.0, 30.0, 20.0, 10.0, 245.0, 100.0, 245.0, 500.0, 255.0, 26950.0, 60000.0, '', '2026-07-06'),
            (106, 'ಪುಡಿ ಉಪ್ಪು (Salt)', 'Salt', 'ಮಸಾಲೆ', 'C06', 15.0, 'ಕೆಜಿ (KG)', 2.0, 5.0, 15.0, 12.0, 10.0, 8.0, 5.0, 57.0, 50.0, 57.0, 100.0, 43.0, 855.0, 5000.0, 'Low Stock Alert triggered for Shraddanjali (2.0 KG)', '2026-07-06'),
            (108, 'ರಾಗಿ (Ragi)', 'Ragi', 'ಧಾನ್ಯಗಳು', 'C01', 35.0, 'ಕೆಜಿ (KG)', 0.0, 0.0, 5.0, 80.0, 15.0, 50.0, 0.0, 150.0, 300.0, 150.0, 500.0, 350.0, 5250.0, 15000.0, 'Low Stock Alert triggered for Boys Hostel (5.0 KG)', '2026-07-06')
        ]
        cursor.executemany("""
            INSERT INTO Grocery_Items
            (Grocery_Code, Grocery_Items_Kan, Grocery_Items_Eng, Grocery_Category, Category_Code, Std_Rate, Qtl_Kg_Ltr,
             Shraddanjali_Qty, Hunnime_Qty, Boys_Hostel_Qty, Girls_Hostel_Qty, Math_Qty, Shantivan_Qty_a, AO_Office_Qty,
             Tot_Quantity, Opening_Stock, Closing_Stock, Tot_Stock, Tot_Issue, Stock_Amt, Total_Budget, Remarks, DateStamp)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """ if db_type == "postgresql" else """
            INSERT INTO Grocery_Items
            (Grocery_Code, Grocery_Items_Kan, Grocery_Items_Eng, Grocery_Category, Category_Code, Std_Rate, Qtl_Kg_Ltr,
             Shraddanjali_Qty, Hunnime_Qty, Boys_Hostel_Qty, Girls_Hostel_Qty, Math_Qty, Shantivan_Qty_a, AO_Office_Qty,
             Tot_Quantity, Opening_Stock, Closing_Stock, Tot_Stock, Tot_Issue, Stock_Amt, Total_Budget, Remarks, DateStamp)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, items)


    # Stock Inward Logs Seed
    inwards = [
        ('2026', '2026-07-01', 101, 2001, None, None, None, None, None, 45.0, 225000.0, 'No', 5000.0, None, 0.0, 0.0, 'ಕೇಂದ್ರ ಗೋದಾಮು', '2026-07-01', 'ಸರ್ಕಾರದಿಂದ ಆಹಾರ ಧಾನ್ಯ ಸರಬರಾಜು', 'Purchase'),
        ('2026', '2026-07-02', 103, 2002, None, None, None, None, None, 120.0, 120000.0, 'No', 1000.0, None, 0.0, 0.0, 'ಕೇಂದ್ರ ಗೋದಾಮು', '2026-07-02', 'ಭಕ್ತರಿಂದ ಕೊಡುಗೆ', 'Donation')
    ]
    cursor.executemany("""
        INSERT INTO Stock_Issue
        (Year1, Date1, Grocery_Code, Shop_Donor_ID, Book_No, Receipt_No, Receipt_Date, Bill_Date, Bill_No, Purchase_Rate, Purchase_Amount, Paid, Stock, Issue_Inst_ID, Issue, Issue_Amount, Received_By, DateStamp, Remarks, Purchased_Donation)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """ if db_type == "postgresql" else """
        INSERT INTO Stock_Issue
        (Year1, Date1, Grocery_Code, Shop_Donor_ID, Book_No, Receipt_No, Receipt_Date, Bill_Date, Bill_No, Purchase_Rate, Purchase_Amount, Paid, Stock, Issue_Inst_ID, Issue, Issue_Amount, Received_By, DateStamp, Remarks, Purchased_Donation)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, inwards)

    # Indents Seeding (Pending, Sent, Received)
    indents = [
        # Pending request
        ('2026', '2026-07-05', 101, 1, 150.0, 'IND-1001', 0.0, 'Pending', None, '2026-07-05', 'ವಾರದ ಅಡುಗೆಗೆ ಬೇಕಾಗಿದೆ'),
        # Sent (Issued but not acknowledged yet)
        ('2026', '2026-07-05', 103, 1, 20.0, 'IND-1002', 20.0, 'Sent', '2026-07-05', '2026-07-05', 'ತುರ್ತು ಬೇಳೆ ಅವಶ್ಯಕತೆ'),
        # Received (Fully completed handshake)
        ('2026', '2026-07-04', 105, 1, 30.0, 'IND-1003', 30.0, 'Received', '2026-07-04', '2026-07-04', 'ತಿಂಗಳ ಅಡುಗೆ ಎಣ್ಣೆ ಕೋಟಾ')
    ]
    cursor.executemany("""
        INSERT INTO Indents
        (Year1, Indent_Date, Grocery_Code, Inst_ID, Quantity, Indent_no, Sanctioned_Quantity, Sanctioned, Sanctioned_on, DateStamp, Remarks)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """ if db_type == "postgresql" else """
        INSERT INTO Indents
        (Year1, Indent_Date, Grocery_Code, Inst_ID, Quantity, Indent_no, Sanctioned_Quantity, Sanctioned, Sanctioned_on, DateStamp, Remarks)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
    """, indents)

    # Insert corresponding issues for completed or active transfers
    issues = [
        ('2026', '2026-07-05', 103, None, None, None, None, None, None, 120.0, 0.0, 'No', 0.0, 1, 20.0, 2400.0, 'ಗುಮಾಸ್ತ ರಾಮಚಂದ್ರ', '2026-07-05', 'IND-1002 ಅನುಮೋದನೆ', 'Issue'),
        ('2026', '2026-07-04', 105, None, None, None, None, None, None, 110.0, 0.0, 'No', 0.0, 1, 30.0, 3300.0, 'ಗುಮಾಸ್ತ ರಾಮಚಂದ್ರ', '2026-07-04', 'IND-1003 ಸ್ವೀಕರಿಸಲಾಗಿದೆ', 'Issue')
    ]
    cursor.executemany("""
        INSERT INTO Stock_Issue
        (Year1, Date1, Grocery_Code, Shop_Donor_ID, Book_No, Receipt_No, Receipt_Date, Bill_Date, Bill_No, Purchase_Rate, Purchase_Amount, Paid, Stock, Issue_Inst_ID, Issue, Issue_Amount, Received_By, DateStamp, Remarks, Purchased_Donation)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """ if db_type == "postgresql" else """
        INSERT INTO Stock_Issue
        (Year1, Date1, Grocery_Code, Shop_Donor_ID, Book_No, Receipt_No, Receipt_Date, Bill_Date, Bill_No, Purchase_Rate, Purchase_Amount, Paid, Stock, Issue_Inst_ID, Issue, Issue_Amount, Received_By, DateStamp, Remarks, Purchased_Donation)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, issues)

    conn.commit()
    conn.close()
    print(f"Database ({db_type}) successfully initialized and seeded with Kannada values.")

if __name__ == '__main__':
    init_db()
