from ultralytics import YOLO
import streamlit as st
import cv2
import settings
import tempfile
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode, RTCConfiguration
import av
import numpy as np
from database import DetectionHistory, SessionLocal
import time
from collections import deque
import threading

model_yolo = None

# Global variables for detection tracking
current_detections = []
detection_history = deque(maxlen=50)
detection_lock = threading.Lock()

def load_model(model_path=settings.DETECTION_MODEL):
    global model_yolo
    if model_yolo is None:
        try:
            model_yolo = YOLO(model_path)
            print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            model_yolo = None
    return model_yolo

class VideoProcessorWaste(VideoProcessorBase):
    def __init__(self, confidence, model):
        self.confidence = confidence
        self.model = model

    def recv(self, frame):
        global current_detections, detection_history, detection_lock
        
        image = frame.to_ndarray(format="bgr24")

        try:
            # Predict the objects in the image using the YOLOv11 model
            res = self.model.predict(image, conf=self.confidence)

            # Plot the detected objects on the video frame
            res_plotted = res[0].plot()
            
            # Extract detection information
            boxes = res[0].boxes
            current_frame_detections = []
            
            if boxes:
                for box in boxes:
                    class_id = int(box.cls)
                    class_name = self.model.names[class_id]
                    conf_value = float(box.conf)
                    current_frame_detections.append({
                        'name': class_name,
                        'confidence': conf_value,
                        'time': time.time()
                    })
            
            # Thread-safe update of global detection variables
            with detection_lock:
                current_detections = current_frame_detections
                if current_frame_detections:
                    detection_history.extend(current_frame_detections)
            
            return av.VideoFrame.from_ndarray(res_plotted, format="bgr24")
            
        except Exception as e:
            # If detection fails, return original frame
            return frame

def display_detection_text():
    """Display current detections and history below webcam"""
    global current_detections, detection_history, detection_lock
    
    # Create containers for detection display
    detection_container = st.container()
    
    with detection_container:
        st.markdown("### ♻️ Deteksi Sampah Real-time")
        
        # Display current detections
        current_col, history_col = st.columns([1, 1])
        
        with current_col:
            st.markdown("**Terdeteksi Saat Ini:**")
            current_placeholder = st.empty()
            
        with history_col:
            st.markdown("**Riwayat Terkini:**")
            history_placeholder = st.empty()
        
        # Control buttons
        control_col1, control_col2, control_col3 = st.columns([1, 1, 1])
        
        with control_col1:
            if st.button("🔄 Refresh", key="refresh_detection"):
                st.rerun()
                
        with control_col2:
            if st.button("🗑️ Bersihkan Riwayat", key="clear_history"):
                with detection_lock:
                    detection_history.clear()
                    current_detections.clear()
                st.success("Riwayat dibersihkan!")
                
        with control_col3:
            show_confidence = st.checkbox("Tampilkan Confidence", value=True)
        
        # Display current detections
        with current_placeholder.container():
            with detection_lock:
                if current_detections:
                    for detection in current_detections:
                        confidence_color = get_confidence_color(detection['confidence'])
                        confidence_text = f" - {detection['confidence']:.2f}" if show_confidence else ""
                        st.markdown(f"{confidence_color} **{detection['name'].upper()}**{confidence_text}")
                else:
                    st.info("🗑️ Tunjukkan sampah ke kamera untuk deteksi...")
        
        # Display recent history
        with history_placeholder.container():
            with detection_lock:
                if detection_history:
                    # Get unique recent detections (last 10 seconds)
                    current_time = time.time()
                    recent_detections = [d for d in detection_history if current_time - d['time'] <= 10]
                    
                    # Group by waste name and show most recent with highest confidence
                    waste_groups = {}
                    for detection in recent_detections:
                        waste_name = detection['name']
                        if waste_name not in waste_groups or detection['confidence'] > waste_groups[waste_name]['confidence']:
                            waste_groups[waste_name] = detection
                    
                    if waste_groups:
                        for waste_name, detection in waste_groups.items():
                            time_ago = current_time - detection['time']
                            confidence_text = f" ({detection['confidence']:.2f})" if show_confidence else ""
                            st.write(f"• {waste_name.upper()}{confidence_text} - {time_ago:.1f}s ago")
                    else:
                        st.write("Tidak ada riwayat terkini")
                else:
                    st.write("Belum ada riwayat")

def get_confidence_color(confidence):
    """Return emoji color based on confidence level"""
    if confidence > 0.8:
        return "🟢"  # Green - Very confident
    elif confidence > 0.6:
        return "🟡"  # Yellow - Moderately confident
    elif confidence > 0.4:
        return "🟠"  # Orange - Low confidence
    else:
        return "🔴"  # Red - Very low confidence

def play_webcam_waste_detection(conf, model):
    """Enhanced webcam function with waste detection display"""
    
    st.markdown("### 📹 Deteksi Sampah Real-time dari Kamera")
    
    # Add troubleshooting info
    with st.expander("🔧 Troubleshooting Webcam"):
        st.markdown("""
        **Jika webcam tidak muncul:**
        - ✅ Pastikan browser memberikan izin akses kamera
        - ✅ Jalankan di `localhost:8501` (bukan IP address)
        - ✅ Refresh halaman jika loading terlalu lama
        - ✅ Coba browser lain (Chrome/Firefox recommended)
        - ✅ Tutup aplikasi lain yang menggunakan kamera
        - ✅ Restart browser jika perlu
        """)

    # Multiple RTC configurations to try
    rtc_configurations = [
        # Configuration 1: Google STUN (Default)
        {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        # Configuration 2: Multiple STUN servers
        {"iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun2.l.google.com:19302"]}
        ]},
        # Configuration 3: No STUN (for local network)
        {"iceServers": []},
        # Configuration 4: Alternative STUN servers
        {"iceServers": [
            {"urls": ["stun:stun.stunprotocol.org:3478"]},
            {"urls": ["stun:stun.ekiga.net:3478"]}
        ]}
    ]
    
    # Let user choose configuration
    config_option = st.selectbox(
        "🔧 Konfigurasi Koneksi:",
        ["Google STUN (Default)", "Multiple STUN", "Lokal (No STUN)", "Alternative STUN"],
        index=0,
        help="Ganti konfigurasi jika webcam tidak muncul"
    )
    
    config_index = ["Google STUN (Default)", "Multiple STUN", "Lokal (No STUN)", "Alternative STUN"].index(config_option)
    selected_config = rtc_configurations[config_index]
    
    try:
        # WebRTC streamer with error handling
        webrtc_ctx = webrtc_streamer(
            key=f"waste_detection_webcam_{config_index}",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=selected_config,
            video_processor_factory=lambda: VideoProcessorWaste(conf, model),
            media_stream_constraints={
                "video": {
                    "width": {"ideal": 640},
                    "height": {"ideal": 480},
                    "frameRate": {"ideal": 15, "max": 30}
                }, 
                "audio": False
            },
            async_processing=True,
        )

        if webrtc_ctx.video_processor:
            webrtc_ctx.video_processor.confidence = conf
            webrtc_ctx.video_processor.model = model
        
        # Status indicator
        if webrtc_ctx.state.playing:
            st.success("✅ Kamera aktif - Mulai deteksi sampah!")
        elif webrtc_ctx.state.signalling:
            st.info("🔄 Menghubungkan ke kamera...")
        else:
            st.info("📷 Klik 'START' untuk memulai deteksi")
            
    except Exception as e:
        st.error(f"❌ Error webcam: {str(e)}")
        st.info("💡 Coba ganti konfigurasi koneksi di dropdown di atas")
        
        # Show fallback option
        st.markdown("---")
        st.markdown("### 📷 Alternatif: Upload Foto")
        st.info("Jika webcam tidak bekerja, gunakan fitur Upload Image di tab 'Image'")
    
    # Add spacing
    st.markdown("---")
    
    # Display detection text below webcam
    display_detection_text()
    
    # Additional features
    with st.expander("📊 Statistik Deteksi Real-time"):
        with detection_lock:
            if detection_history:
                total_detections = len(detection_history)
                unique_waste = len(set(d['name'] for d in detection_history))
                avg_confidence = sum(d['confidence'] for d in detection_history) / len(detection_history)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Deteksi", total_detections)
                with col2:
                    st.metric("Jenis Sampah", unique_waste)
                with col3:
                    st.metric("Rata-rata Confidence", f"{avg_confidence:.2f}")
            else:
                st.info("📊 Belum ada deteksi. Tunjukkan sampah ke kamera!")

# Update fungsi play_webcam_bisindo agar kompatibel
def play_webcam_bisindo(conf, model):
    """Enhanced webcam function for waste detection (keeping original name for compatibility)"""
    
    st.markdown("### 📹 Deteksi Sampah Real-time dari Kamera")
    
    # Add troubleshooting info
    with st.expander("🔧 Troubleshooting Webcam"):
        st.markdown("""
        **Jika webcam tidak muncul:**
        - ✅ Pastikan browser memberikan izin akses kamera
        - ✅ Jalankan di `localhost:8501` (bukan IP address)
        - ✅ Refresh halaman jika loading terlalu lama
        - ✅ Coba browser lain (Chrome/Firefox recommended)
        - ✅ Tutup aplikasi lain yang menggunakan kamera
        - ✅ Restart browser jika perlu
        """)

    # WebRTC configuration with multiple fallbacks
    rtc_config = {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    
    try:
        # WebRTC streamer with error handling
        webrtc_ctx = webrtc_streamer(
            key="waste_detection_webcam",
            mode=WebRtcMode.SENDRECV,
            rtc_configuration=rtc_config,
            video_processor_factory=lambda: VideoProcessorWaste(conf, model),
            media_stream_constraints={
                "video": {
                    "width": {"ideal": 640},
                    "height": {"ideal": 480},
                    "frameRate": {"ideal": 15, "max": 30}
                }, 
                "audio": False
            },
            async_processing=True,
        )

        if webrtc_ctx.video_processor:
            webrtc_ctx.video_processor.confidence = conf
            webrtc_ctx.video_processor.model = model
        
        # Status indicator
        if webrtc_ctx.state.playing:
            st.success("✅ Kamera aktif - Mulai deteksi sampah!")
        elif webrtc_ctx.state.signalling:
            st.info("🔄 Menghubungkan ke kamera...")
        else:
            st.info("📷 Klik 'START' untuk memulai deteksi")
            
    except Exception as e:
        st.error(f"❌ Error webcam: {str(e)}")
        st.info("💡 Silakan coba langkah troubleshooting di atas")
    
    # Add spacing
    st.markdown("---")
    
    # Display detection text below webcam
    display_detection_text()
    
    # Additional features
    with st.expander("📊 Statistik Deteksi Real-time"):
        with detection_lock:
            if detection_history:
                total_detections = len(detection_history)
                unique_waste = len(set(d['name'] for d in detection_history))
                avg_confidence = sum(d['confidence'] for d in detection_history) / len(detection_history)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Deteksi", total_detections)
                with col2:
                    st.metric("Jenis Sampah", unique_waste)
                with col3:
                    st.metric("Rata-rata Confidence", f"{avg_confidence:.2f}")
            else:
                st.info("📊 Belum ada deteksi. Tunjukkan sampah ke kamera!")

def save_detection(source_type, source_path, detected_image):
    from datetime import datetime
    db = SessionLocal()
    try:
        new_record = DetectionHistory(
            source_type=source_type,
            source_path=source_path,
            detected_image=detected_image,
            timestamp=datetime.now()  # Add real timestamp
        )
        db.add(new_record)
        db.commit()
        return new_record.id
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_detection_history():
    db = SessionLocal()
    try:
        # Order by timestamp descending (latest first)
        history = db.query(DetectionHistory).order_by(DetectionHistory.timestamp.desc()).all()
        return history
    except Exception as e:
        raise e
    finally:
        db.close()

def delete_detection_record(record_id):
    db = SessionLocal()
    try:
        record = db.query(DetectionHistory).filter(DetectionHistory.id == record_id).first()
        if record:
            db.delete(record)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def clear_all_detection_history():
    """Clear all detection history from database"""
    db = SessionLocal()
    try:
        # Delete all records
        deleted_count = db.query(DetectionHistory).delete()
        db.commit()
        return deleted_count
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_detection_count():
    """Get total number of detection records"""
    db = SessionLocal()
    try:
        count = db.query(DetectionHistory).count()
        return count
    except Exception as e:
        raise e
    finally:
        db.close()

def get_detection_by_id(record_id):
    """Get single detection record by ID"""
    db = SessionLocal()
    try:
        record = db.query(DetectionHistory).filter(DetectionHistory.id == record_id).first()
        return record
    except Exception as e:
        raise e
    finally:
        db.close()