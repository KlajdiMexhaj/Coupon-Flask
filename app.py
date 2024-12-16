import os
import random
import json
from flask import Flask, render_template, url_for, render_template_string, request,redirect, flash
from flask_admin import Admin
from flask_admin.form import rules
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.base import BaseView, expose
from flask_admin.actions import action
from datetime import datetime
from flask_login import UserMixin, LoginManager, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for Flask-Admin session handling

# Path to store the counter in a file
COUNTER_FILE = "/home/KuponUljeSalus/Coupon-Flask/counter.txt"
CONFIG_FILE = "/home/KuponUljeSalus/Coupon-Flask/config.txt"
EXPIRED_FILE = "/home/KuponUljeSalus/Coupon-Flask/expired.txt"  # To track if the coupon has expired
UPLOAD_FOLDER = '/home/KuponUljeSalus/Coupon-Flask/static/images/'
# File to store IP-to-image mapping
IP_IMAGE_MAPPING_FILE = "/home/KuponUljeSalus/Coupon-Flask/ip_image_mapping.json"

# Helper function to update the visit counter value
def update_counter(counter_value):
    with open(COUNTER_FILE, 'w') as file:
        file.write(str(counter_value))

# Helper function to get the current visit counter value
def get_counter():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'r') as file:
            return int(file.read().strip())
    return 0  # Default value if counter file doesn't exist

# Helper function to get the current counter limit (the value from config.txt)
def get_limit():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return int(file.read().strip())
    return 10  # Default limit if config file doesn't exist

# Helper function to check if the coupon has expired
def is_expired():
    if os.path.exists(EXPIRED_FILE):
        with open(EXPIRED_FILE, 'r') as file:
            return file.read().strip() == '1'
    return False  # Default state if expired file doesn't exist
# Log function to log the API access
def log_api_access():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    api_url = request.url  # Log the full URL of the accessed API
    log_entry = f"{timestamp} - API accessed: {api_url}\n"
def log_VizitorIp(vizitorip):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    api_url = request.url  # Log the full URL of the accessed API
    log_entry = f"{timestamp} - API accessed: {vizitorip}\n"
    # Write to the log file
    with open("api_access_log.txt", "a") as log_file:
        log_file.write(log_entry)

# Helper function to load IP-to-image mapping
def load_ip_image_mapping():
    if os.path.exists(IP_IMAGE_MAPPING_FILE):
        with open(IP_IMAGE_MAPPING_FILE, 'r') as file:
            return json.load(file)
    return {}

# Helper function to save IP-to-image mapping
def save_ip_image_mapping(mapping):
    with open(IP_IMAGE_MAPPING_FILE, 'w') as file:
        json.dump(mapping, file)

# Helper function to get the current counter from ip_image_mapping.json (count of unique IPs)
def get_ip_counter():
    ip_image_mapping = load_ip_image_mapping()
    return len(ip_image_mapping)  # Count how many unique IPs there are

# Helper function to get today's date as a string (YYYY-MM-DD)
def get_today_date():
    return datetime.now().strftime("%Y-%m-%d")

# Helper function to read the last reset date from file
def get_last_reset_date():
    if os.path.exists("last_reset.txt"):
        with open("last_reset.txt", "r") as file:
            return file.read().strip()
    return None  # No reset date found, so we assume it hasn't been reset yet

# Helper function to update the last reset date in the file
def update_last_reset_date():
    today_date = get_today_date()
    with open("last_reset.txt", "w") as file:
        file.write(today_date)
def reset_ip_image_mapping_if_new_day():
    last_reset_date = get_last_reset_date()
    today_date = get_today_date()
    
    # If the date has changed, reset the mapping
    if last_reset_date != today_date:
        # Reset the IP-to-image mapping
        save_ip_image_mapping({})  # Clear the mappings
        
        # Update the last reset date
        update_last_reset_date()








# Set up Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

# In-memory user store for the demo
users = {'admin': {'password': 'admin'}}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:  # Redirect logged-in users
        return redirect(url_for('admin.index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check user credentials
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user, remember=True)
            flash("Logged in successfully!")
            return redirect(url_for('admin.index'))  # Redirect to admin page after login
        else:
            flash("Invalid credentials. Please try again.")

    return '''
        <form method="POST">
            <input type="text" name="username" placeholder="Username"><br>
            <input type="password" name="password" placeholder="Password"><br>
            <button type="submit">Login</button>
        </form>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))




# Admin view to handle counter changes
class CounterAdmin(BaseView):
    @expose('/', methods=('GET', 'POST'))
    @login_required 
    def index(self):
        # Get the visit counter from counter.txt (to track visits)
        counter = get_ip_counter()

        # Get the saved limit from config.txt (this is what will be displayed as current counter)
        limit = get_limit()

        # Check if the coupon has expired
        expired = is_expired()

        image_folder = os.path.join(app.static_folder, 'images')
        images = os.listdir(image_folder) if os.path.exists(image_folder) else []



        # Read the API access log and prepare it for display
        api_log_entries = []
        if os.path.exists("api_access_log.txt"):
            with open("api_access_log.txt", "r") as log_file:
                api_log_entries = log_file.readlines()
                api_access_count = len(api_log_entries) 




        # If the counter has reached the limit, mark it as expired and show the message
        if counter >= limit and not expired:
            
            # Mark as expired
            with open(EXPIRED_FILE, 'w') as file:
                file.write('1')
            return self.render('admin/counter.html', current_counter="Coupon has expired", counter=counter, api_access_count=api_access_count)

        # If the form is submitted, update the limit value
        if request.method == 'POST':
            new_counter = request.form.get('new_counter')
            if new_counter and new_counter.isdigit():
                new_counter = int(new_counter)
                
                # Save the new counter limit to config.txt
                with open(CONFIG_FILE, "w") as config_file:
                    config_file.write(str(new_counter))
                
                # Reset the visit counter and expired state after setting a new limit
                update_counter(0)  # Reset visit counter to 0
                with open(EXPIRED_FILE, 'w') as file:
                    file.write('0')  # Reset expired state

                # After saving, show the new limit value
                return self.render('admin/counter.html', current_counter=new_counter, counter=0, images=images, api_log_entries=api_log_entries, api_access_count=api_access_count)

        # If the coupon has expired, display the "Coupon has expired" message
        if expired:
            return self.render('admin/counter.html', current_counter="Coupon has expired", counter=counter, images=images, api_log_entries=api_log_entries, api_access_count=api_access_count)


        
        # Render the page with the current limit value
        return self.render('admin/counter.html', current_counter=limit, counter=counter,images=images, api_log_entries=api_log_entries, api_access_count=api_access_count)
    
    @expose('/upload_image/', methods=['POST'])
    def upload_image(self):
        # Handle image upload
        if 'image' not in request.files:
            flash("No image uploaded!")
            return redirect(url_for('.index'))

        image = request.files['image']
        if image.filename == '':
            flash("No selected image!")
            return redirect(url_for('.index'))

        # Save the uploaded image
        image.save(os.path.join(UPLOAD_FOLDER, image.filename))
        flash(f"Image {image.filename} uploaded successfully!")
        return redirect(url_for('.index'))   























# Initialize Flask-Admin
admin = Admin(app, name='Counter Admin Panel', template_mode='bootstrap3')

# Add CounterAdmin to the admin panel
admin.add_view(CounterAdmin(name='CouponAdmin'))

@app.route('/')
def home():
    # Reset the IP-image mapping if the day has changed
    reset_ip_image_mapping_if_new_day()
    
    # Load the IP-to-image mapping
    ip_image_mapping = load_ip_image_mapping()
    
    # Get the visitor's IP address
    visitor_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if visitor_ip:
        visitor_ip = visitor_ip.split(',')[0]
    
    log_VizitorIp(visitor_ip)  # Log the visitor's IP
    
    # Get the counter limit from the configuration file
    counter_limit = get_limit()
    # Log the access of the current API (this will log the full URL)
    log_api_access()

    # Get the current counter from ip_image_mapping.json (this counts unique IPs)
    counter = get_ip_counter()

    if counter >= counter_limit and counter_limit > 0:
        # Display "Coupon has expired" message if the counter exceeds the limit
        return render_template_string("<h1>Coupon has expired</h1>")
    
    # Handle random image display
    image_folder = os.path.join(app.static_folder, 'images')  # Path to the images folder
    images = os.listdir(image_folder)  # List all files in the images folder
    if not images:
        return "<h1>No images found</h1>"

    # If this is a new visitor IP (first visit), assign an image and increment the counter
    if visitor_ip not in ip_image_mapping:
        assigned_image = random.choice(images)
        ip_image_mapping[visitor_ip] = assigned_image
        
        # Increment the counter since this is a first-time visit
        save_ip_image_mapping(ip_image_mapping)  # Save updated IP-to-image mapping

    else:
        assigned_image = ip_image_mapping[visitor_ip]

    image_url = url_for('static', filename=f'images/{assigned_image}')  # Get URL for the image
    # Render the home.html template and pass the counter and image_url to it
    return render_template('home.html', current_counter=counter_limit, counter=counter, image_url=image_url)




# Route to delete an image
@app.route('/delete_image/<image_name>', methods=['POST'])
def delete_image(image_name):
    image_path = os.path.join(UPLOAD_FOLDER, image_name)
    if os.path.exists(image_path):
        os.remove(image_path)
        flash(f"Image {image_name} deleted successfully.")
    else:
        flash(f"Image {image_name} does not exist.")
    return redirect(url_for('counteradmin.index'))





















if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)