from io import BytesIO
import os
import pickle
import shutil
from tkinter import Label, filedialog, ttk
from fpdf import FPDF
import numpy as np
import cv2
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
import numpy as np
from datetime import datetime
import threading
from time import time
import pandas as pd
from windowcapture import WindowCapture  # Add window capture library
import pygetwindow as gw
import tkinter as tk
from tkinter import Toplevel, Canvas, Scrollbar
from tkinter import PhotoImage
from PIL import Image, ImageTk

cred = credentials.Certificate("baigiamasisServiceKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://baigiamasis-darbas-cea75-default-rtdb.firebaseio.com/",
    'storageBucket': "baigiamasis-darbas-cea75.appspot.com"
})

ref = db.reference('Students')

bucket = storage.bucket()

# Create the tkinter GUI
def create_menu():

    global is_recognition_active
    global is_statistics_active
    global is_view_faces_active
    is_statistics_active = False
    is_recognition_active = False
    is_view_faces_active = False

    def start_face_recognition_screen_capture():
        global is_recognition_active
        if not is_recognition_active:
            is_recognition_active = True
            video_thread = threading.Thread(target=capture_video)
            video_thread.start()

    def start_face_recognition_webcam_capture():
        global is_recognition_active
        if not is_recognition_active:
            is_recognition_active = True
            video_thread = threading.Thread(target=capture_video_webcam)
            video_thread.start()

    def start_view_faces_capture():
        global is_view_faces_active
        if not is_view_faces_active:
            is_view_faces_active = True
            video_thread = threading.Thread(target=view_faces)
            video_thread.start()

    def view_faces():
       
        global is_view_faces_active
        is_view_faces_active = True

        # Retrieve the list of student IDs from the database
        student_ids = db.reference('Students').get()

        # Create a new window to display the faces
        faces_window = Toplevel()
        faces_window.title("Manage Students")

        # Create a canvas for displaying the faces with a scrollbar
        canvas = Canvas(faces_window)
        canvas.pack(side="left", fill="both", expand=True)

        # Create a scrollbar for vertical scrolling
        scrollbar = Scrollbar(faces_window, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        # Configure the canvas to use the scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create a frame inside the canvas to contain the elements
        frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor="nw")

        # Function to update student information
        def update_student(student_id, name, major, group, starting_year):
            try:
                # Reference to the student in the database
                student_ref = db.reference(f'Students/{student_id}')

                # Update the student's data in the database
                student_ref.update({
                    'name': name,
                    'major': major,
                    'group': group,
                    'starting_year': starting_year,
                })
                print(f"Updated student {student_id} successfully.")
            except Exception as e:
                print(f"An error occurred: {e}")

        def delete_student(student_id):
            try:
                # Reference to the student in the database
                student_ref = db.reference(f'Students/{student_id}')
                student_ref.delete()  # Delete the student record from the database
                print(f"Deleted student {student_id} from database successfully.")

                # Create a reference to the storage bucket
                bucket = storage.bucket()

                # Create a blob reference to the student's image
                blob = bucket.blob(f'Images/{student_id}.png')
                blob.delete()  # Delete the student's image from Firebase Storage
                student_frame.destroy()  # Remove the student's frame from the GUI
                print(f"Deleted image for student {student_id} from storage successfully.")
            except Exception as e:
                print(f"An error occurred while deleting student {student_id}: {e}")


        def get_and_display_image(student_id, frame, size=(100, 100)):
            # Create a reference to the storage bucket
            bucket = storage.bucket()

            # Create a blob reference to the student's image
            blob = bucket.blob(f'Images/{student_id}.png')

            # Download the contents of the blob into memory
            try:
                img_data = blob.download_as_bytes()
                img_pil = Image.open(BytesIO(img_data))

                # Resize the image while maintaining aspect ratio
                img_pil.thumbnail(size, Image.ANTIALIAS)

                img_tk = ImageTk.PhotoImage(img_pil)

                # Create a label and assign the image
                image_label = Label(frame, image=img_tk)
                image_label.image = img_tk  # Keep a reference to prevent garbage collection
                image_label.pack()

                return image_label

            except Exception as e:
                print(f"An error occurred: {e}")
                # Handle the exception (e.g., display a default image or an error message)
                return None

        # Populate the frame with face images and information
        for student_id in student_ids:
            student_info = db.reference(f'Students/{student_id}').get()

            student_frame = ttk.Frame(frame)
            student_frame.pack(fill='x', expand=True)

            # Get and display the image, along with capturing the returned image label
            image_label = get_and_display_image(student_id, student_frame, size=(100, 100))

            name = student_info['name']
            major = student_info['major']
            group = student_info['group']
            starting_year = student_info['starting_year']

            # Create labels and entry fields for the student information
            name_label = ttk.Label(student_frame, text="Name:")
            name_entry = ttk.Entry(student_frame)
            name_entry.insert(0, name)
            major_label = ttk.Label(student_frame, text="Major:")
            major_entry = ttk.Entry(student_frame)
            major_entry.insert(0, major)
            group_label = ttk.Label(student_frame, text="Group:")
            group_entry = ttk.Entry(student_frame)
            group_entry.insert(0, group)
            starting_year_label = ttk.Label(student_frame, text="Starting Year:")
            starting_year_entry = ttk.Entry(student_frame)
            starting_year_entry.insert(0, starting_year)

            # Buttons to update user info, add a new image, and delete the user
            update_button = ttk.Button(student_frame, text="Update", command=lambda sid=student_id, n=name_entry, m=major_entry, g=group_entry, sy=starting_year_entry: update_student(sid, n.get(), m.get(), g.get(), sy.get()))
            delete_button = ttk.Button(student_frame, text="Delete", command=lambda sid=student_id: delete_student(sid))

            # Pack the widgets into the student_frame
            name_label.pack(side="top", fill="x")
            name_entry.pack(side="top", fill="x")
            major_label.pack(side="top", fill="x")
            major_entry.pack(side="top", fill="x")
            group_label.pack(side="top", fill="x")
            group_entry.pack(side="top", fill="x")
            starting_year_label.pack(side="top", fill="x")
            starting_year_entry.pack(side="top", fill="x")
            update_button.pack(side="top", fill="x")
            delete_button.pack(side="top", fill="x")

                    
            # Update the canvas to fit the content
            frame.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))  

    def view_statistics():
         global is_statistics_active
         if not is_statistics_active:
            is_statistics_active = True
            statistics_thread = threading.Thread(target=show_statistics)
            statistics_thread.start()


    # Function to get the latest image number
    def get_latest_image_number(folder_path):
        image_files = os.listdir(folder_path)
        # Extract numbers from image names and sort them
        image_numbers = [int(os.path.splitext(image)[0]) for image in image_files if os.path.splitext(image)[0].isdigit()]
        if image_numbers:  # Check if the list is not empty
            return max(image_numbers)
        else:
            return 0  # Return 0 if no images are found

    # Function to get the latest image number from Firebase Storage
    def get_latest_image_number():
        bucket = storage.bucket()
        # List all objects in the 'Images' bucket
        blobs = bucket.list_blobs(prefix='Images/')
        image_numbers = [int(blob.name.split('/')[-1].split('.')[0]) for blob in blobs if blob.name.split('/')[-1].split('.')[0].isdigit()]
        return max(image_numbers) if image_numbers else 0

    # Modified function to handle adding a student and image with the new naming convention
    def add_student_and_image(name, major, group, starting_year, image_path):
        # Check if any of the fields is empty
        if not all([name, major, group, starting_year, image_path]):
            print("All fields, including the image, must be filled out.")
            return

        # Get the latest image number and add 1 for the new image name
        latest_image_number = get_latest_image_number()
        new_image_number = latest_image_number + 1
        student_id = str(new_image_number)

        # Upload the image to Firebase Storage
        bucket = storage.bucket()
        file_extension = os.path.splitext(image_path)[1]
        new_file_name = f"Images/{new_image_number}{file_extension}"
        blob = bucket.blob(new_file_name)
        blob.upload_from_filename(image_path)
        print(f"Picture saved as {new_file_name}")

        # Construct the student data dictionary with the Firebase Storage path to the image
        student_data = {
            'name': name,
            'major': major,
            'group': group,
            'starting_year': starting_year,
            'total_attendance': 0,  # Initialize total_attendance
            'last_attendance_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Initialize with current time
        }

        # Add the student data to Firebase Realtime Database under the student ID key
        db.reference('Students').child(student_id).set(student_data)
        print(f"Student {name} added successfully with ID {student_id}.")

    # Function to create the add student window
    def create_add_student_window():
        root = tk.Tk()
        root.title("Add Student to Database")

        tk.Label(root, text="Name:").pack()
        name_entry = tk.Entry(root)
        name_entry.pack()

        tk.Label(root, text="Major:").pack()
        major_entry = tk.Entry(root)
        major_entry.pack()

        tk.Label(root, text="Group:").pack()
        group_entry = tk.Entry(root)
        group_entry.pack()

        tk.Label(root, text="Starting Year:").pack()
        starting_year_entry = tk.Entry(root)
        starting_year_entry.pack()

        select_image_label = tk.Label(root, text="Select Image:")
        select_image_label.pack()

        entry_image_path = tk.Entry(root)
        entry_image_path.pack()

        select_image_button = tk.Button(root, text="Browse", command=lambda: select_image(entry_image_path))
        select_image_button.pack()

        add_button = tk.Button(root, text="Add User", command=lambda: add_student_and_image(
            name_entry.get(),
            major_entry.get(),
            group_entry.get(),
            starting_year_entry.get(),
            entry_image_path.get(),
        ))
        add_button.pack()

        root.mainloop()

    # Function to select an image and save the path in the entry widget
    def select_image(entry_widget):
        file_path = filedialog.askopenfilename(title="Select a picture file", filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, file_path)

    def raise_frame(frame):
        frame.tkraise()

    root = tk.Tk()
    root.title("Face Recognition Program")

    # size of the window
    root.geometry('600x400')

    # a style for the buttons
    style = ttk.Style()
    style.theme_use('alt')  # Use an alternative theme
    style.configure('TButton', font=('Helvetica', 12), padding=10)
    style.map('TButton', background=[('active', '#ececec')])

    # creating a frame for button placement
    main_frame = ttk.Frame(root, padding="10")
    main_frame.pack(expand=True, fill="both")

    # using ttk.Button to apply the style
    webcam_face_recognition_button = ttk.Button(main_frame, text="Webcam Face Recognition", command=start_face_recognition_webcam_capture)
    screen_face_recognition_button = ttk.Button(main_frame, text="Screen Face Recognition", command=start_face_recognition_screen_capture)
    view_faces_button = ttk.Button(main_frame, text="View Faces", command=start_view_faces_capture)
    view_statistics_button = ttk.Button(main_frame, text="View Statistics", command=view_statistics)
    add_new_student_button = ttk.Button(main_frame, text="Add Student", command=create_add_student_window)

    # placing buttons on the main_frame with padding in between
    webcam_face_recognition_button.pack(fill='x', pady=5)
    screen_face_recognition_button.pack(fill='x', pady=5)
    view_faces_button.pack(fill='x', pady=5)
    view_statistics_button.pack(fill='x', pady=5)
    add_new_student_button.pack(fill='x', pady=5)

    root.mainloop()

def capture_video():
    global is_recognition_active

    # Get the chosen window title
    window_name = choose_window_with_dropdown()

    # Initialize the WindowCapture class with the chosen window name
    wincap = WindowCapture(window_name)

    # Importing the mode images into a list
    folderModePath = 'Resources/Modes'
    modePathList = os.listdir(folderModePath)
    imgModeList = []
    for path in modePathList:
        imgModeList.append(cv2.imread(os.path.join(folderModePath, path)))

    # Load the encoding file
    print("Loading Encode File ...")
    file = open('EncodeFile.p', 'rb')
    encodeListKnownWithIds = pickle.load(file)
    file.close()
    encodeListKnown, studentIds = encodeListKnownWithIds
    print("Encode File Loaded")

    modeType = 0
    counter = 0
    recognized_ids = set()
    imgStudents = []

    loop_time = time()
    while is_recognition_active:
        # Get an updated image of the chosen window
        screenshot = wincap.get_screenshot()

        imgS = cv2.resize(screenshot, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        faceCurFrame = face_recognition.face_locations(imgS)
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

        if faceCurFrame:
            recognized_ids.clear()

            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

                matchIndex = np.argmin(faceDis)

                if matches[matchIndex]:
                    id = studentIds[matchIndex]
                    recognized_ids.add(id)

                    studentInfo = db.reference(f'Students/{id}').get()
                    name = studentInfo['name']  # Get the name of the recognized person

                    if counter == 0:
                        cv2.imshow("Face Attendance", screenshot)
                        cv2.waitKey(1)
                        counter = 1
                        modeType = 1

                    # Draw a rectangle around the face
                    (top, right, bottom, left) = faceLoc
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4
                    cv2.rectangle(screenshot, (left, top), (right, bottom), (0, 0, 255), 2)

                    # Display the name below the drawn rectangle
                    cv2.putText(screenshot, name, (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            if counter != 0:

                if counter == 1:
                    for id in recognized_ids:
                        # Get the Data
                        studentInfo = db.reference(f'Students/{id}').get()
                        print(studentInfo)
                        # Get the Image from the storage
                        if id not in imgStudents:
                            blob = bucket.get_blob(f'Images/{id}.png')
                            array = np.frombuffer(blob.download_as_string(), np.uint8)
                            imgStudents.append(cv2.imdecode(array, cv2.COLOR_BGRA2BGR))

                        # Update data of attendance
                        datetimeObject = datetime.strptime(studentInfo['last_attendance_time'],
                                                           "%Y-%m-%d %H:%M:%S")
                        secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                        print(secondsElapsed)
                        if secondsElapsed > 30:
                            ref = db.reference(f'Students/{id}')
                            studentInfo['total_attendance'] += 1
                            ref.child('total_attendance').set(studentInfo['total_attendance'])
                            ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # Display the image
        cv2.imshow("Face Attendance", screenshot)

        # Check for the 'q' key to quit the program
        key = cv2.waitKey(1)
        if key == ord('q'):
            is_recognition_active = False

    cv2.destroyAllWindows()

def capture_video_webcam():
    global is_recognition_active

    # Load the encoding file
    print("Loading Encode File ...")
    with open('EncodeFile.p', 'rb') as file:
        encodeListKnownWithIds = pickle.load(file)
    encodeListKnown, studentIds = encodeListKnownWithIds
    print("Encode File Loaded")

    # Initialize the webcam
    video_capture = cv2.VideoCapture(0)

    # Set of recognized student IDs
    recognized_ids = set()

    while is_recognition_active:
        # Capture a single frame from the webcam
        ret, frame = video_capture.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Resize the captured frame to 1/4 size for faster face recognition processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Convert the image from BGR to RGB
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Find all the face locations and face encodings in the current frame
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        recognized_ids.clear()

        for face_encoding, face_location in zip(face_encodings, face_locations):
            # See if the face is a match for the known faces
            matches = face_recognition.compare_faces(encodeListKnown, face_encoding)
            face_distances = face_recognition.face_distance(encodeListKnown, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index]:
                student_id = studentIds[best_match_index]
                recognized_ids.add(student_id)

                # Retrieve student info from the database
                student_info = db.reference(f'Students/{student_id}').get()
                
                # Ensure student_info is not None
                if student_info:
                    name = student_info['name']

                    # Draw a rectangle around the face and display the name
                    top, right, bottom, left = [i * 4 for i in face_location]  # Scale back up to the original image size
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                    cv2.putText(frame, name, (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

                    update_attendance(student_id, student_info)
                else:
                    print(f"No data found for student ID: {student_id}")

        # Display the resulting image
        cv2.imshow('Webcam Face Recognition', frame)

        # Hit 'q' on the keyboard to quit the program
        if cv2.waitKey(1) & 0xFF == ord('q'):
            is_recognition_active = False

    # Release the webcam and close all OpenCV windows
    video_capture.release()
    cv2.destroyAllWindows()


def update_attendance(student_id, student_info):
    # Get the last attendance time from the student info
    datetime_object = datetime.strptime(student_info['last_attendance_time'], "%Y-%m-%d %H:%M:%S")
    seconds_elapsed = (datetime.now() - datetime_object).total_seconds()

    # If it has been more than 30 seconds since last recognized, update the attendance
    if seconds_elapsed > 30:
        ref = db.reference(f'Students/{student_id}')
        total_attendance = student_info.get('total_attendance', 0) + 1
        ref.update({
            'total_attendance': total_attendance,
            'last_attendance_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })


def export_to_pdf(data, save_path):
    pdf = FPDF()
    
    # Set default column width in case there are more columns than specified widths
    default_width = 40
    # Define column widths, if there are more columns than widths, default will be used
    column_widths = [40, 60]  # Example widths for 2 columns

    # Add a page
    pdf.add_page()

    # Set font
    pdf.set_font("Arial", size=12)

    # Add a cell for the title if needed
    pdf.cell(0, 10, txt="Attendance Report", ln=True, align='C')

    # Header
    for i, column in enumerate(data.columns):
        # Use specified width if available, otherwise use the default width
        col_width = column_widths[i] if i < len(column_widths) else default_width
        pdf.cell(col_width, 10, txt=column.capitalize(), border=1)
    pdf.ln(10)

    # Data
    for row in data.itertuples(index=False):  # index=False to avoid including the index
        for i, value in enumerate(row):
            # Use specified width if available, otherwise use the default width
            col_width = column_widths[i] if i < len(column_widths) else default_width
            pdf.cell(col_width, 10, txt=str(value), border=1)
        pdf.ln(10)

    # Save the pdf with name .pdf
    pdf.output(save_path)

# Function to export the data to a file
def export_data(student_info):
    save_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[
            ("CSV files", "*.csv"),
            ("Excel files", "*.xlsx"),  # Changed to '.xlsx'
            ("Text files", "*.txt"),
            ("PDF files", "*.pdf")
        ]
    )
    
    if save_path:
        extension = os.path.splitext(save_path)[-1].lower()

        # Convert the data into a pandas DataFrame
        data = pd.DataFrame.from_dict(student_info, orient='index')
        
        if extension == '.csv':
            data.to_csv(save_path, index=False)
        elif extension == '.xlsx':  # Changed to '.xlsx'
            # Export to .xlsx format with openpyxl
            data.to_excel(save_path, index=False, engine='openpyxl')
        elif extension == '.txt':
            data.to_csv(save_path, sep='\t', index=False)
        elif extension == '.pdf':
            export_to_pdf(data, save_path)

        print("Data exported successfully.")

# Function to display and export statistics from the database
def show_statistics():
    global is_statistics_active
    is_statistics_active = True

    # Retrieve statistics data from the database
    # Assume db is a predefined database connection
    student_info = db.reference('Students').get()

    # Create a new window to display statistics
    statistics_window = tk.Tk()
    statistics_window.title("Statistics")

    # Display the statistics data in the window
    for student_id, data in student_info.items():
        student_label = tk.Label(statistics_window, text=f"ID: {student_id}, Name: {data['name']}, Last Attendance Time: {data['last_attendance_time']}, Total Attendance: {data['total_attendance']}, Major: {data['major']}")
        student_label.pack()

    # Add a button to close the statistics window
    close_button = tk.Button(statistics_window, text="Close", command=statistics_window.destroy)
    close_button.pack()

    # Add a button to export the statistics data
    export_button = tk.Button(statistics_window, text="Export", command=lambda: export_data(student_info))
    export_button.pack()

    statistics_window.mainloop()
    is_statistics_active = False


def choose_window_with_dropdown():
    # Create a new instance of Tkinter
    root = tk.Tk()
    root.title("Select Window for Capture")

    # Get the list of window titles
    windows = gw.getAllTitles()
    windows = [w for w in windows if w]  # Remove any empty strings

    # Variable to store the selection
    window_selection = tk.StringVar(root)

    # Create a dropdown box
    dropdown = ttk.Combobox(root, textvariable=window_selection)
    dropdown['values'] = windows
    dropdown['state'] = 'readonly'  # Prevent user from typing a value
    dropdown.pack(pady=10, padx=10)

    # Function to handle button click
    def on_select():
        root.quit()

    # Create a select button
    select_button = ttk.Button(root, text="Select", command=on_select)
    select_button.pack(pady=5, padx=10)

    # Run the Tkinter event loop
    root.mainloop()

    # Destroy the root window
    root.destroy()

    # Return the selected window title
    return window_selection.get()


# Start the menu creation
create_menu()
