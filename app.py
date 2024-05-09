
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from celery_worker import scrape_website
import sqlite3
from flask import make_response
import io
from flask import Flask
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from auth import User, get_user_by_username, load_user

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'
# Example Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.user_loader(load_user)


# Database connection setup
def get_db_connection():
    conn = sqlite3.connect('scraping_results.db')
    return conn

# Create the results table if it doesn't exist
def create_results_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS results
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 url TEXT,
                 keyword TEXT,
                 h1_count INTEGER,
                 h2_count INTEGER,
                 body_count INTEGER)''')
    conn.commit()
    conn.close()

create_results_table()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)
        if user:
            print(f"User data: {user.id}, {user.username}, {user.password}")
        else:
            print("User not found")
        if user and user.password == password:
            user_obj = User(user.id, user.username, user.password)
            login_user(user_obj)
            return redirect('/gsc')
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/gsc/login')


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect('/gsc')
    else:
        return redirect('/gsc/login')


@app.route('/gsc')
@login_required
def gsc_index():
    return render_template('index.html')
    
    

@login_required
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    
    # Save the uploaded file
    file.save('uploaded_file.xlsx')

    # Process the uploaded file
    df = pd.read_excel('uploaded_file.xlsx')

    # Clear the existing results from the database
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM results')
    conn.commit()
    conn.close()

    # Insert the scraping tasks into the database
    task_ids = []
    for _, row in df.iterrows():
        url = row['URL']
        keyword = row['Keyword']
        result = scrape_website.delay(url, keyword)
        task_ids.append(result.id)

    return jsonify({"message": "File uploaded and processing started", "task_ids": task_ids})


@app.route('/tasks_status', methods=['POST'])
def get_tasks_status():
    task_ids = request.json['task_ids']
    
    task_statuses = []
    for task_id in task_ids:
        task_result = scrape_website.AsyncResult(task_id)
        task_statuses.append(task_result.ready())
    
    all_tasks_completed = all(task_statuses)
    
    return jsonify({"all_tasks_completed": all_tasks_completed})


@login_required
@app.route('/results')
def get_results():
    # Retrieve the scraping results from the database
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT url, keyword, h1_count, h2_count, body_count FROM results')
    results = c.fetchall()
    conn.close()

    # Format the results as a list of dictionaries
    formatted_results = []
    for result in results:
        formatted_result = {
            'url': result[0],
            'keyword': result[1],
            'h1_count': result[2],
            'h2_count': result[3],
            'body_count': result[4]
        }
        formatted_results.append(formatted_result)

    return jsonify(formatted_results)


@login_required
@app.route('/download')
def download_results():
    try:
        # Retrieve the scraping results from the database
        conn = sqlite3.connect('scraping_results.db')
        c = conn.cursor()
        c.execute('SELECT url, keyword, h1_count, h2_count, body_count FROM results')
        results = c.fetchall()
        conn.close()

        # Create a pandas DataFrame with the results
        df = pd.DataFrame(results, columns=['URL', 'Keyword', 'H1 Count', 'H2 Count', 'Body Count'])

        # Create an Excel file in memory
        excel_data = io.BytesIO()
        df.to_excel(excel_data, index=False, sheet_name='Sheet1')

        # This line moves the pointer to the beginning of the in-memory buffer
        excel_data.seek(0)

        # Prepare the response with the Excel file attached
        response = make_response(excel_data.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=results.xlsx'
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return response

    except Exception as e:
        # Handle any exceptions that may occur
        print(f"ERROR:root:An error occurred while generating the Excel file.")
        print(e)
        return "An error occurred while generating the Excel file.", 500
    
if __name__ == '__main__':
    app.run(debug=True)