@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"🔐 Login attempt - Username: '{username}'")
        print(f"🔐 Login attempt - Password: '{password}'")
        
        if not username or not password:
            flash('Please enter both username and password', 'danger')
            return render_template('login.html')
        
        if db:
            user = db.authenticate_user(username, password)
            if user:
                login_user(User(user))
                db.log_activity(user['id'], 'login', {'method': 'web'}, 
                              ip=request.remote_addr, user_agent=request.headers.get('User-Agent'))
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            else:
                print("❌ Authentication failed - invalid credentials")
                flash('Invalid username or password', 'danger')
        else:
            flash('Database connection unavailable', 'danger')
    
    return render_template('login.html')
