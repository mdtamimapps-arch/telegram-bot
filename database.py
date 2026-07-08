import sqlite3

def get_db():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            deposit INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            description TEXT,
            paid_by TEXT,
            amount INTEGER,
            category TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS special_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            amount INTEGER,
            category TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_name TEXT,
            bill_type TEXT,
            amount INTEGER,
            paid BOOLEAN DEFAULT 0,
            paid_by TEXT,
            month_year TEXT,
            UNIQUE(member_name, bill_type, month_year)
        )
    ''')
    
    conn.commit()
    return conn

def init_data():
    conn = get_db()
    cursor = conn.cursor()

    # সদস্যদের মিলের জমা
    members = [
        ('আকাশ', 500), ('প্রান্ত', 500), ('সামিউল', 1000),
        ('তামীম', 1000), ('মেহেদী', 1000), ('সাইফ', 500),
        ('সাম্য', 1000), ('লালন', 1000)
    ]
    for name, deposit in members:
        cursor.execute('INSERT OR IGNORE INTO members (name, deposit) VALUES (?, ?)', (name, deposit))

    # সাইফের বিশেষ জমা
    cursor.execute('INSERT OR IGNORE INTO special_expenses (name, amount, category) VALUES (?, ?, ?)',
                   ('সাইফ', 6000, 'বাসা+ওয়াইফাই+কারেন্ট'))

    # মিলের খরচ
    expenses = [
        ('2026-06-30', 'চাল', 'তামীম+লালন', 120, 'মিল'),
        ('2026-07-01', 'বাজার', 'প্রান্ত+আকাশ', 4790, 'মিল')
    ]
    for date, desc, paid, amount, cat in expenses:
        cursor.execute('INSERT OR IGNORE INTO expenses (date, description, paid_by, amount, category) VALUES (?, ?, ?, ?, ?)',
                       (date, desc, paid, amount, cat))

    # বিলের ডেটা (বাসা ভাড়া ও কমন বিল)
    rent_map = {
        'সাইফ': 2625, 'লালন': 2625, 'সাম্য': 2625,
        'তামীম': 2450, 'সামিউল': 2450,
        'প্রান্ত': 2300, 'আকাশ': 2300,
        'মেহেদী': 2625
    }
    common_bills = {'গ্যাস': 450, 'ওয়াইফাই': 80, 'খালা বিল': 650, 'বিদ্যুৎ': 0}

    for name in [m[0] for m in members]:
        rent = rent_map.get(name, 2625)
        cursor.execute('''
            INSERT OR IGNORE INTO bills (member_name, bill_type, amount, paid, paid_by, month_year)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, 'বাসা ভাড়া', rent, 0, None, '2026-07'))

        for bill_type, amount in common_bills.items():
            cursor.execute('''
                INSERT OR IGNORE INTO bills (member_name, bill_type, amount, paid, paid_by, month_year)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, bill_type, amount, 0, None, '2026-07'))

    # সাইফ ওয়াইফাই পরিশোধ করেছে
    cursor.execute('''
        UPDATE bills SET paid = 1, paid_by = 'সাইফ'
        WHERE member_name = 'সাইফ' AND bill_type = 'ওয়াইফাই' AND month_year = '2026-07'
    ''')

    conn.commit()
    conn.close()

# ------- ফাংশনসমূহ -------
def get_total_deposit():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(deposit) FROM members')
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

def get_total_expenses():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(amount) FROM expenses WHERE category="মিল"')
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

def get_member_deposit(name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT deposit FROM members WHERE name=?', (name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def get_special_expense(name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT amount, category FROM special_expenses WHERE name=?', (name,))
    result = cursor.fetchone()
    conn.close()
    return result if result else None

def get_all_expenses():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT date, description, paid_by, amount FROM expenses ORDER BY date')
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_new_expense(date, desc, paid_by, amount):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO expenses (date, description, paid_by, amount, category) VALUES (?, ?, ?, ?, ?)',
                   (date, desc, paid_by, amount, 'মিল'))
    conn.commit()
    conn.close()

def get_member_bills(name, month='2026-07'):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT bill_type, amount, paid, paid_by FROM bills
        WHERE member_name = ? AND month_year = ?
    ''', (name, month))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_member_expenses(name):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT date, description, amount FROM expenses
        WHERE paid_by LIKE ? AND category='মিল'
    ''', (f'%{name}%',))
    rows = cursor.fetchall()
    conn.close()
    return rows
