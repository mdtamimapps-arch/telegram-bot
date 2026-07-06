import sqlite3

def get_db():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    # সদস্য টেবিল
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            deposit INTEGER DEFAULT 0
        )
    ''')
    # খরচ টেবিল (মিলের)
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
    # বিশেষ খরচ (সাইফের বাসা+ওয়াইফাই+কারেন্ট)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS special_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            amount INTEGER,
            category TEXT
        )
    ''')
    # 📌 নতুন: বিল টেবিল (প্রতি সদস্যের বিলের বিবরণ)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_name TEXT,
            bill_type TEXT,
            amount INTEGER,
            paid BOOLEAN DEFAULT 0,
            paid_by TEXT,
            month_year TEXT
        )
    ''')
    conn.commit()
    return conn

def init_data():
    conn = get_db()
    cursor = conn.cursor()

    # --- ১. সদস্যদের জমা (মিলের) ---
    members = [
        ('আকাশ', 500), ('প্রান্ত', 500), ('সামিউল', 1000),
        ('তামীম', 1000), ('মেহেদী', 1000), ('সাইফ', 500),
        ('সাম্য', 1000), ('লালন', 1000)
    ]
    for name, deposit in members:
        cursor.execute('INSERT OR IGNORE INTO members (name, deposit) VALUES (?, ?)', (name, deposit))

    # --- ২. সাইফের বিশেষ জমা (বাসা+ওয়াইফাই+কারেন্ট) ---
    cursor.execute('INSERT OR IGNORE INTO special_expenses (name, amount, category) VALUES (?, ?, ?)',
                   ('সাইফ', 6000, 'বাসা+ওয়াইফাই+কারেন্ট'))

    # --- ৩. মিলের খরচ (ইতিমধ্যে দেয়া) ---
    expenses = [
        ('2026-06-30', 'চাল', 'তামীম+লালন', 120, 'মিল'),
        ('2026-07-01', 'বাজার', 'প্রান্ত+আকাশ', 4790, 'মিল')
    ]
    for date, desc, paid, amount, cat in expenses:
        cursor.execute('INSERT OR IGNORE INTO expenses (date, description, paid_by, amount, category) VALUES (?, ?, ?, ?, ?)',
                       (date, desc, paid, amount, cat))

    # --- ৪. 📌 ডিফল্ট বিলের ডেটা (প্রতি সদস্যের) ---
    # বাসা ভাড়া (আলাদা)
    rent_map = {
        'সাইফ': 2625, 'লালন': 2625, 'সাম্য': 2625,
        'তামীম': 2450, 'সামিউল': 2450,
        'প্রান্ত': 2300, 'আকাশ': 2300,
        'মেহেদী': 2625  # মেহেদীর জন্য সাইফের সাথে একই ধরে নিচ্ছি (আপনি চাইলে বদলাতে পারেন)
    }
    # সাধারণ বিল (সবার জন্য একই)
    common_bills = {
        'গ্যাস': 450,
        'ওয়াইফাই': 80,    # প্রতি জনের ভাগ (মোট ৬৪০ হলে ৮ জনে ৮০)
        'খালা বিল': 650,
        'বিদ্যুৎ': 0       # আলোচনা সাপেক্ষে
    }

    # প্রতিটি সদস্যের জন্য বিল তৈরি করুন
    for name in [m[0] for m in members]:
        # বাসা ভাড়া
        rent = rent_map.get(name, 2625)  # ডিফল্ট ২৬২৫
        cursor.execute('''
            INSERT OR IGNORE INTO bills (member_name, bill_type, amount, paid, paid_by, month_year)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, 'বাসা ভাড়া', rent, 0, None, '2026-07'))

        # সাধারণ বিল
        for bill_type, amount in common_bills.items():
            cursor.execute('''
                INSERT OR IGNORE INTO bills (member_name, bill_type, amount, paid, paid_by, month_year)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, bill_type, amount, 0, None, '2026-07'))

    # --- ৫. বিশেষ কিছু বিলের স্থিতি আপডেট (যেমন সাইফ ওয়াইফাই দিয়েছে) ---
    # সাইফ ওয়াইফাই বিল (তার ভাগ ৮০, কিন্তু সে ৬৩০ দিয়েছে – ধরে নিচ্ছি পুরো বিল বা বাড়তি)
    # এখানে আমরা শুধু সাইফের ওয়াইফাই বিলকে 'paid' করছি
    cursor.execute('''
        UPDATE bills SET paid = 1, paid_by = 'সাইফ'
        WHERE member_name = 'সাইফ' AND bill_type = 'ওয়াইফাই' AND month_year = '2026-07'
    ''')

    # সামিউল: মিল থেকে ১০০০ নেওয়া হয়েছে (আমরা expenses-এ যোগ করতে পারি, কিন্তু সে বিল বাকি রেখেছে)
    # তাই বিল টেবিলে কোনো পরিবর্তন নয়, বরং expenses টেবিলে তার খরচ যোগ করা যেতে পারে।
    # কিন্তু user বলেছে "সামিউল এর মিলের ১০০০ টাকা দেওয়া হইয়াছে কিন্তু বাসা ভাড়া ... দেয়নি"
    # অর্থাৎ তার বিলগুলো এখনো unpaid আছে, যা ডিফল্ট 0 থাকবে।

    conn.commit()
    conn.close()

# --- ফাংশনগুলো (পূর্বের মতো) ---
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

# --- 📌 নতুন ফাংশন: সদস্যের সব বিল ও পরিশোধের তথ্য ---
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

# --- সদস্যের মিল সংক্রান্ত খরচ (তার পক্ষ থেকে) ---
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
