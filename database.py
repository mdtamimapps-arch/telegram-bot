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
    conn.commit()
    return conn

def init_data():
    conn = get_db()
    cursor = conn.cursor()
    # মিলের জমা
    members = [
        ('আকাশ', 500), ('প্রান্ত', 500), ('সামিউল', 1000),
        ('তামীম', 1000), ('মেহেদী', 1000), ('সাইফ', 500),
        ('সাম্য', 1000), ('লালন', 1000)
    ]
    for name, deposit in members:
        cursor.execute('INSERT OR IGNORE INTO members (name, deposit) VALUES (?, ?)', (name, deposit))
    
    # সাইফের বিশেষ জমা (৬০০০ টাকা)
    cursor.execute('INSERT OR IGNORE INTO special_expenses (name, amount, category) VALUES (?, ?, ?)',
                   ('সাইফ', 6000, 'বাসা+ওয়াইফাই+কারেন্ট'))
    
    # খরচ যোগ করুন
    expenses = [
        ('2026-06-30', 'চাল', 'তামীম+লালন', 120, 'মিল'),
        ('2026-07-01', 'বাজার', 'প্রান্ত+আকাশ', 4790, 'মিল')
    ]
    for date, desc, paid, amount, cat in expenses:
        cursor.execute('INSERT OR IGNORE INTO expenses (date, description, paid_by, amount, category) VALUES (?, ?, ?, ?, ?)',
                       (date, desc, paid, amount, cat))
    conn.commit()
    conn.close()

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