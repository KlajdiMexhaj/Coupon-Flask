import os
import random
from flask import Flask, render_template, url_for, render_template_string, request,redirect, flash
from flask_admin import Admin
from flask_admin.form import rules
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.base import BaseView, expose
from flask_admin.actions import action
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for Flask-Admin session handling

# Path to store the counter in a file
COUNTER_FILE = "counter.txt"
CONFIG_FILE = "config.txt"
EXPIRED_FILE = "expired.txt"  # To track if the coupon has expired
UPLOAD_FOLDER = 'static/images/'

# Helper function to get the visit counter value from counter.txt
def get_counter():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, 'r') as file:
            return int(file.read().strip())
    return 0  # Default value if counter file doesn't exist

# Helper function to update the visit counter value in counter.txt
def update_counter(counter_value):
    with open(COUNTER_FILE, 'w') as file:
        file.write(str(counter_value))

# Helper function to get the current counter limit (the value from config.txt)
def get_limit():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return int(file.read().strip())
    return 10  # Default limit if config file doesn't exist

# Helper function to check if the counter has expired
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
    
    # Write to the log file
    with open("api_access_log.txt", "a") as log_file:
        log_file.write(log_entry)
















# Admin view to handle counter changes
class CounterAdmin(BaseView):
    @expose('/', methods=('GET', 'POST'))
    def index(self):
        # Get the visit counter from counter.txt (to track visits)
        counter = get_counter()

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
    # Get the counter limit from the configuration file
    counter_limit = get_limit()
    # Log the access of the current API (this will log the full URL)
    log_api_access()
    
    # Handle counter logic
    counter = get_counter()
    if counter >= counter_limit and counter_limit > 0:
        # Display "Coupon has expired" message if the counter exceeds the limit
        return render_template_string("<h1>Coupon has expired</h1>")
    
    # Increment counter
    counter += 1
    update_counter(counter)
    
    # Handle random image display
    image_folder = os.path.join(app.static_folder, 'images')  # Path to the images folder
    images = os.listdir(image_folder)  # List all files in the images folder
    if not images:
        return "<h1>No images found</h1>"
    
    random_image = random.choice(images)  # Pick a random image
    image_url = url_for('static', filename=f'images/{random_image}')  # Get URL for the image
    
    # Render the home.html template and pass the counter and image_url to it
    return render_template('home.html', counter=counter, image_url=image_url)



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
    app.run(debug=True)