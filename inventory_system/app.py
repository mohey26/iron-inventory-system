from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime
import sqlite3, csv, io

app = Flask(__name__)
DATABASE = 'inventory.db'

def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cur = db.cursor()
    cur.executescript('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            type VARCHAR(100),
            length FLOAT,
            weight FLOAT,
            location VARCHAR(100),
            min_stock INTEGER DEFAULT 10,
            barcode VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS current_stock (
            product_id INTEGER PRIMARY KEY,
            quantity INTEGER DEFAULT 0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS incoming (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            product_id INTEGER NOT NULL,
            supplier VARCHAR(150),
            quantity INTEGER NOT NULL,
            unit_price FLOAT DEFAULT 0,
            total_price FLOAT DEFAULT 0,
            notes TEXT,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS outgoing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            product_id INTEGER NOT NULL,
            purpose VARCHAR(150),
            quantity INTEGER NOT NULL,
            notes TEXT,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            message TEXT,
            alert_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_read INTEGER DEFAULT 0,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
    ''')
    db.commit()
    db.close()

def check_low_stock(db, product_id):
    cur = db.cursor()
    cur.execute('SELECT p.min_stock, cs.quantity FROM products p JOIN current_stock cs ON p.id=cs.product_id WHERE p.id=?', (product_id,))
    row = cur.fetchone()
    if row and row['quantity'] < row['min_stock']:
        cur.execute('INSERT INTO alerts (product_id, message) VALUES (?, ?)',
                    (product_id, f"المخزون منخفض ({row['quantity']} قطعة)"))
        db.commit()

# ----------- المسارات -----------
@app.route('/')
def dashboard():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT COUNT(*) as cnt FROM products')
    total_products = cur.fetchone()['cnt']
    cur.execute('SELECT SUM(quantity) as total FROM current_stock')
    total_qty = cur.fetchone()['total'] or 0
    cur.execute('''SELECT 'in' as type, i.date, p.name, i.quantity FROM incoming i
                   JOIN products p ON i.product_id=p.id
                   UNION ALL
                   SELECT 'out' as type, o.date, p.name, o.quantity FROM outgoing o
                   JOIN products p ON o.product_id=p.id
                   ORDER BY date DESC LIMIT 5''')
    movements = cur.fetchall()
    cur.execute('''SELECT a.*, p.name, p.code FROM alerts a
                   JOIN products p ON a.product_id=p.id
                   WHERE a.is_read=0 ORDER BY a.alert_date DESC''')
    alerts = cur.fetchall()
    db.close()
    return render_template('dashboard.html', total_products=total_products,
                           total_qty=total_qty, movements=movements, alerts=alerts)

@app.route('/products')
def products_list():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT p.*, cs.quantity FROM products p LEFT JOIN current_stock cs ON p.id=cs.product_id ORDER BY p.code')
    products = cur.fetchall()
    db.close()
    return render_template('products.html', products=products)

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute('INSERT INTO products (code, name, type, length, weight, location, min_stock, barcode) VALUES (?,?,?,?,?,?,?,?)',
                    (data['code'], data['name'], data.get('type'), data.get('length'),
                     data.get('weight'), data.get('location'), data.get('min_stock',10), data.get('barcode')))
        pid = cur.lastrowid
        cur.execute('INSERT INTO current_stock (product_id, quantity) VALUES (?,0)', (pid,))
        db.commit()
        db.close()
        return jsonify({'ok': True, 'message': 'تمت الإضافة'})
    except Exception as e:
        db.close()
        return jsonify({'ok': False, 'message': str(e)}), 400

@app.route('/incoming')
def incoming_page():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id, code, name FROM products ORDER BY code')
    products = cur.fetchall()
    db.close()
    return render_template('incoming.html', products=products)

@app.route('/api/incoming', methods=['POST'])
def add_incoming():
    data = request.json
    db = get_db()
    cur = db.cursor()
    try:
        price = float(data.get('unit_price',0)) * float(data['quantity'])
        cur.execute('INSERT INTO incoming (date, product_id, supplier, quantity, unit_price, total_price, notes) VALUES (?,?,?,?,?,?,?)',
                    (data['date'], data['product_id'], data.get('supplier'), data['quantity'],
                     data.get('unit_price',0), price, data.get('notes')))
        cur.execute('UPDATE current_stock SET quantity = quantity + ? WHERE product_id = ?',
                    (data['quantity'], data['product_id']))
        check_low_stock(db, data['product_id'])
        db.commit()
        db.close()
        return jsonify({'ok': True, 'message': 'تم تسجيل الوارد'})
    except Exception as e:
        db.close()
        return jsonify({'ok': False, 'message': str(e)}), 400

@app.route('/outgoing')
def outgoing_page():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id, code, name FROM products ORDER BY code')
    products = cur.fetchall()
    db.close()
    return render_template('outgoing.html', products=products)

@app.route('/api/outgoing', methods=['POST'])
def add_outgoing():
    data = request.json
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute('SELECT quantity FROM current_stock WHERE product_id=?', (data['product_id'],))
        row = cur.fetchone()
        if not row or row['quantity'] < int(data['quantity']):
            db.close()
            return jsonify({'ok': False, 'message': 'الكمية غير كافية'}), 400
        cur.execute('INSERT INTO outgoing (date, product_id, purpose, quantity, notes) VALUES (?,?,?,?,?)',
                    (data['date'], data['product_id'], data.get('purpose'), data['quantity'], data.get('notes')))
        cur.execute('UPDATE current_stock SET quantity = quantity - ? WHERE product_id = ?',
                    (data['quantity'], data['product_id']))
        check_low_stock(db, data['product_id'])
        db.commit()
        db.close()
        return jsonify({'ok': True, 'message': 'تم تسجيل الصادر'})
    except Exception as e:
        db.close()
        return jsonify({'ok': False, 'message': str(e)}), 400

@app.route('/reports')
def reports_page():
    return render_template('reports.html')

@app.route('/api/report')
def get_report():
    start = request.args.get('start')
    end = request.args.get('end')
    db = get_db()
    cur = db.cursor()
    cur.execute('''SELECT p.name, p.code,
                  COALESCE(in_sum.qty,0) as total_in,
                  COALESCE(out_sum.qty,0) as total_out,
                  COALESCE(cs.quantity,0) as stock_now
               FROM products p
               LEFT JOIN (SELECT product_id, SUM(quantity) as qty FROM incoming
                          WHERE date BETWEEN ? AND ? GROUP BY product_id) in_sum ON p.id=in_sum.product_id
               LEFT JOIN (SELECT product_id, SUM(quantity) as qty FROM outgoing
                          WHERE date BETWEEN ? AND ? GROUP BY product_id) out_sum ON p.id=out_sum.product_id
               LEFT JOIN current_stock cs ON p.id=cs.product_id
               ORDER BY p.code''',
               (start, end, start, end))
    rows = [dict(r) for r in cur.fetchall()]
    db.close()
    return jsonify(rows)

@app.route('/export/csv')
def export_csv():
    start = request.args.get('start','')
    end = request.args.get('end','')
    db = get_db()
    cur = db.cursor()
    cur.execute('''SELECT p.name, p.code,
                  COALESCE(in_sum.qty,0) as وارد,
                  COALESCE(out_sum.qty,0) as صادر,
                  COALESCE(cs.quantity,0) as المخزون
               FROM products p
               LEFT JOIN (SELECT product_id, SUM(quantity) as qty FROM incoming
                          WHERE date BETWEEN ? AND ? GROUP BY product_id) in_sum ON p.id=in_sum.product_id
               LEFT JOIN (SELECT product_id, SUM(quantity) as qty FROM outgoing
                          WHERE date BETWEEN ? AND ? GROUP BY product_id) out_sum ON p.id=out_sum.product_id
               LEFT JOIN current_stock cs ON p.id=cs.product_id
               ORDER BY p.code''', (start, end, start, end))
    rows = [dict(r) for r in cur.fetchall()]
    db.close()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['المنتج','الكود','إجمالي الوارد','إجمالي الصادر','المخزون الحالي'])
    for r in rows:
        cw.writerow([r['name'], r['code'], r['وارد'], r['صادر'], r['المخزون']])
    output = si.getvalue().encode('utf-8-sig')
    return send_file(io.BytesIO(output), mimetype='text/csv', as_attachment=True, download_name=f'taqrir_{start}_{end}.csv')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
