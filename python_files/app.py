from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename

#initiate the app 
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shifts.db'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}
app.secret_key = 'your_secret_key'

#initiate databse 
db = SQLAlchemy(app)
#shift model

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Unique ID for each shift
    name = db.Column(db.String(100), nullable=False)  # Employee name
    date = db.Column(db.Date, nullable=False)  # Shift date
    time_started = db.Column(db.String(5), nullable=False)  # Time shift started (HH:MM)
    time_ended = db.Column(db.String(5), nullable=False)  # Time shift ended (HH:MM)
    photo_filename = db.Column(db.String(100))  # Filename of uploaded shift report image

    def __repr__(self):
        return f'<Shift {self.id}>'

# Function to check if uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Route to upload shift report
@app.route('/', methods=['GET', 'POST'])
def upload_shift():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        date = request.form['date']
        time_started = request.form['time_started']
        time_ended = request.form['time_ended']
        photo = request.files['photo']
        
        # Handle file upload
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = None  # No valid file uploaded
            
            
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()
        
        #create new shit
        new_shift = Shift(name=name, date=date_obj, time_started=time_started, time_ended=time_ended, photo_filename=filename)
        db.session.add(new_shift)
        db.session.commit()
        
        return redirect(url_for('upload_shift')) #redirect to the same page 
    return render_template('web_page_files/templates/index.html') # upload form

        #route to generate the excel 
        
@app.route(' /generate_report')
def generate_report():
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=15)  # Get the last 15 days
    
    shifts = Shift.query.filter(Shift.date >=start_date, Shift.date <= end_date).all()
    
    data = []
    total_hours = 0 # variable to track total
    
    #process each shift 
    for Shift in Shift:
        start = datetime.strptime(Shift.time_started, '%H:%M')
        end = datetime.strptime(Shift.time_ended, '%H:%M')
        hours_worked = (end - start).seconds/3600 # convertion 
        total_hours += hours_worked
        data.append([Shift.name, Shift.date, Shift.time_started, Shift.time_ended, hours_worked, Shift.photo_filename])
        
    df = pd.DataFrame(data, columns=['Name', 'Date', 'Time Started', 'Time Ended', 'Hours Worked', 'Photo']) 

    df.loc[len(df)]= ['Total','','','',total_hours,''] # append total hours
    
    # Export to excel
    excel_filename = f"Shift_report_{start_date}_{end_date}.xlsx"
    df.to_excel(excel_filename,index=False)
    
    return f"Report generated successfully: {excel_filename}"

#route to se all the shift in the dashboard
@app.route('/view_shifts')
def view_Shifts():
    shifts = Shift.query.all() # fetch everything 
    return render_template('web_page_files/templates/view_shifts.html', shifts=shifts)

# run flask app


if __name__ == "__main__":
    db.create_all()  # create tables if not already done
    app.run(debug=True) # start in debuge mode
    
    


        