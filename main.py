import csv
import qrcode
from pyzbar.pyzbar import decode
import cv2
import streamlit as st
import pandas as pd
from streamlit_webrtc import VideoTransformerBase, webrtc_streamer




st.set_page_config(page_title="Check in",
                   layout="wide",
                   page_icon=":clipboard:",)

# ************************************ Variables ************************************

# Chemin vers la liste des participants (fichier csv)


class VideoTransformer(VideoTransformerBase):
    def __init__(self):
        self.threshold1 = 100
        self.threshold2 = 200

    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")

        img = cv2.cvtColor(
            cv2.Canny(img, self.threshold1, self.threshold2), cv2.COLOR_GRAY2BGR
        )

        return img


if "csv_file_path" not in st.session_state:
    st.session_state.csv_file_path ='Attendees.csv'

if "attendees_df" not in st.session_state:
    st.session_state.attendees_df =pd.read_csv(st.session_state.csv_file_path)



# ************************************ Functions ************************************

# Fonction pour lire les données à partir du fichier CSV


# Fonction pour générer un code QR
def generate_qr_code(data):
    for attendee in data:
        qr_content = f"ID: {attendee['ID']}, Name: {attendee['Name']}, Last Name: {attendee['Last Name']}, OLM: {attendee['OLM']}"
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(qr_content)
        qr.make(fit=True)
        qr_image_filename = f"QR_{attendee['ID']}.png"
        qr.make_image(fill_color="black", back_color="white").save(qr_image_filename)
        print(f"QR code generated for {attendee['Name']} {attendee['Last Name']}")

# Fonction pour gérer l'événement de numérisation du code QR
def on_qr_scan(frame_placeholder):
    while True:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            # If index 0 fails, try index 1
            cap = cv2.VideoCapture(1)
            if not cap.isOpened():
                # Neither index 0 nor index 1 worked
                st.error("Unable to open video capture device.")
        ret, frame = cap.read()
        colors = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_placeholder.image(colors,channels="RGB",width=500)
        decoded_objects = decode(colors)
        #cv2.imshow('frame', frame)
        if decoded_objects:
            qr_content = decoded_objects[0].data.decode('utf-8')
            success_msg=update_attendance(qr_content)
            print(success_msg)
            break
    cap.release()
    cv2.destroyAllWindows()
    frame_placeholder=st.empty()
    st.rerun()
def qr_data_read(qr_content):
    qr_content_splitted = qr_content.split(',')
    qr_data={}
    for qr_single_content in qr_content_splitted:
        column=qr_single_content.split(':')[0].lstrip()
        value=qr_single_content.split(':')[1].lstrip()
        if column not in qr_data.keys():
            qr_data[column] = value
    return qr_data
# Fonction pour mettre à jour la présence dans le fichier CSV
def update_attendance(qr_content):
    qr_data=qr_data_read(qr_content)
    for index, attendee in st.session_state.attendees_df.iterrows():
        if attendee['ID'] == int(qr_data['ID']):
            if attendee['Attendance']==False:
                st.session_state.attendees_df.at[index, 'Attendance'] = True
                st.session_state.attendees_df.to_csv(st.session_state.csv_file_path,index=False)
                success_msg=f"Attendance updated for {qr_data['Name']} {qr_data['Last Name']}, attendee ID: {qr_data['ID']}"
                return(success_msg)
            else:
                error_msg=f"Attendance already updated for {qr_data['Name']} {qr_data['Last Name']}, attendee ID: {qr_data['ID']}"
                return(error_msg)

    


# ************************************ Page ************************************

# ********** Trick to preserve the state of your widgets across pages
for k, v in st.session_state.items():
    st.session_state[k] = v
# **********


st.markdown(
    """
    ### **Check in**
    
    """, 
    unsafe_allow_html=True
)

with st.sidebar:
    st.header('Check in Web App')
    









# Exemple d'utilisation
if __name__ == "__main__":
    start_recording=st.button("Activate Camera")
    frame_placeholder=st.empty()
    st.write(st.session_state.attendees_df)
    #generate_qr_code(attendees_data)
    #if start_recording:
        #on_qr_scan(frame_placeholder)
    ctx = webrtc_streamer(key="example", video_transformer_factory=VideoTransformer)

    if ctx.video_transformer:
        ctx.video_transformer.threshold1 = st.slider("Threshold1", 0, 1000, 100)
        ctx.video_transformer.threshold2 = st.slider("Threshold2", 0, 1000, 200)
