# Import modules
from pathlib import Path
import PIL
import tempfile
import cv2
import base64
import streamlit as st
from datetime import datetime
import io

# Local Modules
import settings
import helper

# Setting page layout
st.set_page_config(
    page_title="Deteksi Sampah Organik dan Anorganik",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Customizing the sidebar and main content with enhanced styling
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@400;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Rubik', sans-serif !important;
        }

        .custom-header {
            background: linear-gradient(135deg, #2E7D32, #4CAF50);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .custom-header h2 {
            color: white;
            margin: 0;
            font-weight: 600;
        }
        .history-image {
            width: 100%;
            max-width: 350px;
            height: auto;
            border-radius: 10px;
        }
        .main-title {
            font-size: 42px;
            font-weight: 700;
            color: #2E7D32;
            margin-bottom: 15px;
            text-align: center;
        }

        .subtext {
            font-size: 18px;
            line-height: 1.6;
            color: #333;
            margin-bottom: 25px;
            text-align: center;
        }

        .info-card {
            background: linear-gradient(135deg, #E8F5E8, #F1F8E9);
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 25px;
            border-left: 5px solid #4CAF50;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }

        .info-card h3 {
            color: #2E7D32;
            font-size: 22px;
            margin-bottom: 15px;
            font-weight: 600;
        }

        .waste-type-card {
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 2px solid #E0E0E0;
            transition: all 0.3s ease;
        }

        .waste-type-card:hover {
            border-color: #4CAF50;
            box-shadow: 0 4px 15px rgba(76, 175, 80, 0.1);
        }

        .organic-card {
            border-left: 5px solid #4CAF50;
        }

        .inorganic-card {
            border-left: 5px solid #FF9800;
        }

        .detection-result {
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin: 15px 0;
            border-left: 4px solid #4CAF50;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .confidence-high { color: #4CAF50; font-weight: 600; }
        .confidence-medium { color: #FF9800; font-weight: 600; }
        .confidence-low { color: #F44336; font-weight: 600; }

        .stApp {
            background-color: #f8fffe;
        }

        .stButton > button {
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            transition: all 0.3s ease;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, #45a049, #3d8b40);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
        }

        .timestamp {
            font-size: 12px;
            color: #666;
            font-style: italic;
        }
    </style>
    """, unsafe_allow_html=True)

# Enhanced sidebar with custom header
st.sidebar.markdown('<div class="custom-header"><h2>♻️ EcoDetect</h2></div>', unsafe_allow_html=True)

page = st.sidebar.selectbox("Pilih Halaman", ["🏠 Beranda", "🔍 Deteksi", "📚 Riwayat"], index=0, key='page_selector')

def resize_to_fixed_height(image, height):
    """Resize image to fixed height while maintaining aspect ratio"""
    aspect_ratio = image.width / image.height
    width = int(height * aspect_ratio)
    return image.resize((width, height))

# Home Page
if page == "🏠 Beranda":
    st.markdown("<div class='main-title'>♻️ Selamat Datang di EcoDetect ♻️</div>", unsafe_allow_html=True)

    st.markdown("""
        <div class='subtext'>
            Aplikasi berbasis web yang menggunakan <strong>YOLOv11</strong> untuk mendeteksi dan mengklasifikasikan 
            <strong>sampah organik dan anorganik</strong> dari gambar atau kamera secara real-time. 
            Dirancang untuk mendukung pengelolaan sampah yang lebih baik dan ramah lingkungan.
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class='info-card'>
            <h3>📱 Fitur Aplikasi</h3>
            <ul style="list-style-type: none; padding-left: 0;">
                <li style="margin: 8px 0;"><strong>🏠 Beranda</strong>: Informasi aplikasi dan jenis sampah yang dapat dideteksi.</li>
                <li style="margin: 8px 0;"><strong>🔍 Deteksi</strong>: Upload gambar atau gunakan kamera untuk mendeteksi jenis sampah.</li>
                <li style="margin: 8px 0;"><strong>📚 Riwayat</strong>: Lihat dan kelola hasil deteksi sebelumnya.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    # Example detection images
    st.markdown("### 🔬 Contoh Hasil Deteksi")
    st.markdown("<p style='text-align: center; color: #666; margin-bottom: 20px;'>Berikut adalah perbandingan gambar sebelum dan sesudah proses deteksi</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        try:
            # Use images from your folder
            default_image_path = "images/sebelumdeteksi.jpg"
            default_image = PIL.Image.open(default_image_path)
            st.image(default_image_path, caption="📷 Gambar Asli", use_container_width=True)
        except:
            # Fallback to settings default image if available
            try:
                default_image_path = str(settings.DEFAULT_IMAGE)
                default_image = PIL.Image.open(default_image_path)
                st.image(default_image_path, caption="📷 Gambar Asli", use_container_width=True)
            except:
                st.info("Gambar contoh tidak tersedia")
    
    with col2:
        try:
            # Use images from your folder
            default_detected_image_path = "images/hasildeteksi.jpg"
            default_detected_image = PIL.Image.open(default_detected_image_path)
            st.image(default_detected_image_path, caption="🎯 Hasil Deteksi YOLOv11", use_container_width=True)
        except:
            # Fallback to settings default detected image if available
            try:
                default_detected_image_path = str(settings.DEFAULT_DETECT_IMAGE)
                default_detected_image = PIL.Image.open(default_detected_image_path)
                st.image(default_detected_image_path, caption="🎯 Hasil Deteksi YOLOv11", use_container_width=True)
            except:
                st.info("Gambar hasil deteksi tidak tersedia")

    # Waste types information section
    st.markdown("---")
    st.markdown("### 📚 Informasi Jenis-Jenis Sampah atau Objek Terdeteksi")

    # Organic waste section
    st.markdown("""
        <div class='waste-type-card organic-card'>
            <h4 style='color: #4CAF50; margin-bottom: 15px;'>🌱 Sampah Organik</h4>
        </div>
    """, unsafe_allow_html=True)

    # Biodegradable waste
    st.markdown("#### 🌱 Sampah Biodegradable")
    
    # Display example image if available
    try:
        biodegradable_image = PIL.Image.open("images/biodegradable.jpg")
        resized_bio = resize_to_fixed_height(biodegradable_image, 200)
        st.image(resized_bio, caption="Contoh Sampah Biodegradable", use_container_width=False)
    except Exception as e:
        st.info("📷 Gambar contoh tidak tersedia")

    st.markdown("""
    **Deskripsi**: Sampah organik adalah sampah yang berasal dari sisa-sisa organisme makhluk hidup baik manusia, hewan, serta tumbuhan. Sampah organik merupakan jenis sampah yang mudah terurai melalui proses alami.

    ### Cara Pengelolaan:
    - 🌿 **Kompos**: Bisa diolah menjadi pupuk kompos untuk tanaman.
    - 🔄 **Digunakan Kembali**: Beberapa bahan biodegradable bisa digunakan sebagai pakan ternak atau bahan kerajinan.
    - 🧺 **Pisahkan dari Anorganik**: Penting untuk memilah sampah biodegradable agar tidak tercampur dengan plastik atau logam.

    Sumber: [Detik - Sampah Organik Adalah: Jenis, Contoh, Manfaat dan Cara Mengolah](https://www.detik.com/jabar/berita/d-6262012/sampah-organik-adalah-jenis-contoh-manfaat-dan-cara-mengolah)
    """)

    # Paper waste
    st.markdown("#### 📄 Kertas")
    
    try:
        paper_image = PIL.Image.open("images/kertas.jpg")
        resized_paper = resize_to_fixed_height(paper_image, 200)
        st.image(resized_paper, caption="Contoh Sampah Kertas", use_container_width=False)
    except Exception as e:
        st.info("📷 Gambar contoh tidak tersedia")

    st.markdown("""
    **Deskripsi**: Kertas masuk ke dalam kategori sampah yang mudah untuk terurai, walaupun membutuhkan waktu yang berbeda-beda.

    ### Cara Pengelolaan:
    - ♻️ **Daur Ulang**: Kertas yang bersih dan kering dapat dikumpulkan dan dijual ke pengepul atau bank sampah.
    - ✂️ **Gunakan Ulang**: Kertas bekas dapat digunakan untuk catatan, kerajinan tangan, atau pembungkus.
    - 🧺 **Pisahkan**: Hindari mencampur kertas dengan sampah basah agar tidak rusak dan tetap bernilai daur ulang.

    Sumber: [Kumparan - Kertas Termasuk Sampah Organik atau Anorganik?](https://kumparan.com/ragam-info/kertas-termasuk-sampah-organik-atau-anorganik-ini-penjelasannya-22bvXIk8GXZ/3)
    """)

    # Inorganic waste section
    st.markdown("""
        <div class='waste-type-card inorganic-card'>
            <h4 style='color: #FF9800; margin-bottom: 15px;'>🏭 Sampah Anorganik</h4>
        </div>
    """, unsafe_allow_html=True)

    # Metal cans
    st.markdown("#### 🥤 Kaleng Minuman")
    
    try:
        can_image = PIL.Image.open("images/kaleng.jpeg")
        resized_can = resize_to_fixed_height(can_image, 200)
        st.image(resized_can, caption="Contoh Kaleng Minuman Anorganik", use_container_width=False)
    except Exception as e:
        st.info("📷 Gambar contoh tidak tersedia")

    st.markdown("""
    **Deskripsi**: Sampah logam mencakup kaleng bekas minuman, tin, atau berbagai benda logam lainnya. Logam seperti alumunium dan besi memerlukan proses daur ulang khusus karena sulit terurai di alam. Sampah logam yang dibuang sembarangan dapat mencemari tanah dan air, sehingga pengelolaannya harus lebih diperhatikan.

    ### Cara Pengelolaan:
    - ♻️ **Daur Ulang**: Kaleng dapat didaur ulang menjadi produk logam baru.
    - 🚮 **Pemisahan Sampah**: Penting untuk memisahkan kaleng dari sampah organik sebelum dibuang.
    - 📦 **Pengumpulan Massal**: Biasanya dikumpulkan dalam bank sampah atau posko daur ulang.

    Sumber: [Rekosistem - Sampah Anorganik: Pengertian, Jenis, dan Cara Pengelolaannya](https://rekosistem.com/2025/02/03/sampah-anorganik-pengertian-jenis-dan-cara-pengelolaannya/)
    """)

    # Glass waste
    st.markdown("#### 🥛 Kaca (Botol / Pecahan Kaca)")
    
    try:
        glass_image = PIL.Image.open("images/kaca.jpg")
        resized_glass = resize_to_fixed_height(glass_image, 200)
        st.image(resized_glass, caption="Contoh Sampah Kaca", use_container_width=False)
    except Exception as e:
        st.info("📷 Gambar contoh tidak tersedia")

    st.markdown("""
    **Deskripsi**: Sampah kaca meliputi botol, gelas, dan berbagai benda kaca lainnya. Kaca merupakan material yang tidak mudah terurai dan dapat mencemari lingkungan jika dibuang sembarangan. Namun, kaca adalah salah satu material yang dapat didaur ulang dengan efisien, sehingga pengelolaan yang baik sangat penting untuk mengurangi dampaknya.

    ### Cara Pengelolaan:
    - ♻️ **Daur Ulang**: Kaca dapat dilebur dan dibentuk kembali menjadi produk baru seperti botol atau bahan bangunan.
    - ⚠️ **Pemilahan Hati-hati**: Pecahan kaca harus dipisahkan dari sampah lain dan dikemas agar tidak melukai petugas kebersihan.
    - 📦 **Pengumpulan Terpisah**: Botol kaca utuh bisa dikumpulkan di bank sampah atau drop box khusus.

    Sumber: [Rekosistem - Sampah Anorganik: Pengertian, Jenis, dan Cara Pengelolaannya](https://rekosistem.com/2025/02/03/sampah-anorganik-pengertian-jenis-dan-cara-pengelolaannya/)
    """)

    # Plastic bottles
    st.markdown("#### 🧴 Botol Plastik")
    
    try:
        bottle_image = PIL.Image.open("images/botol.jpg")
        resized_bottle = resize_to_fixed_height(bottle_image, 200)
        st.image(resized_bottle, caption="Contoh Botol Plastik", use_container_width=False)
    except Exception as e:
        st.info("📷 Gambar contoh tidak tersedia")

    st.markdown("""
    **Deskripsi**: Sampah plastik adalah semua barang bekas atau tidak terpakai yang materialnya diproduksi dari bahan kimia tak terbarukan. Sebagian besar sampah plastik yang digunakan sehari-hari biasanya dipakai untuk pengemasan.

    ### Cara Pengelolaan:
    - ♻️ **Daur Ulang**: Botol plastik bisa dikumpulkan, dicuci, dan diproses menjadi biji plastik untuk digunakan kembali.
    - 🚯 **Hindari Pembakaran**: Membakar plastik menghasilkan zat beracun yang berbahaya bagi kesehatan dan lingkungan.
    - 📦 **Pisahkan dengan Rapi**: Botol sebaiknya dipipihkan dan dipisahkan dari sampah organik sebelum dibuang.

    Sumber: [dlh.bulelengkab - SAMPAH PLASTIK DI SEKITAR KITA](https://dlh.bulelengkab.go.id/informasi/detail/artikel/17_sampah-plastik-di-sekitar-kita-antara-kebutuhan-dan-masalah-yang-ditimbulkan)
    """)

# Detection Page
elif page == "🔍 Deteksi":
    st.title("♻️ Deteksi Sampah Organik dan Anorganik menggunakan YOLO11")

    st.sidebar.header("Konfigurasi Model ML")
    confidence = float(st.sidebar.slider("Pilih Kepercayaan Model (%)", 25, 100, 40)) / 100

    model_path = Path(settings.DETECTION_MODEL)
    try:
        model = helper.load_model(model_path)
    except Exception as ex:
        st.error(f"Tidak dapat memuat model. Periksa path yang ditentukan: {model_path}")
        st.error(ex)

    st.sidebar.subheader("Konfigurasi Gambar/Webcam")
    source_radio = st.sidebar.radio("Pilih Sumber", settings.SOURCES_LIST)

    source_img = None

    # If image is selected
    if source_radio == settings.IMAGE:
        source_img = st.sidebar.file_uploader("Pilih gambar...", type=("jpg", "jpeg", "png", 'bmp', 'webp'))

        col1, col2 = st.columns(2)

        with col1:
            try:
                if source_img is None:
                    default_image_path = str(settings.DEFAULT_IMAGE)
                    default_image = PIL.Image.open(default_image_path)
                    st.image(default_image_path, caption="Gambar Default", use_container_width=True)
                else:
                    uploaded_image = PIL.Image.open(source_img)
                    st.image(source_img, caption="Gambar yang Diupload", use_container_width=True)
            except Exception as ex:
                st.error("Error terjadi saat membuka gambar.")
                st.error(ex)

        with col2:
            if source_img is None:
                default_detected_image_path = str(settings.DEFAULT_DETECT_IMAGE)
                default_detected_image = PIL.Image.open(default_detected_image_path)
                st.image(default_detected_image_path, caption='Gambar Terdeteksi', use_container_width=True)
            else:
                if st.sidebar.button('Deteksi Objek'):
                    try:
                        res = model.predict(uploaded_image, conf=confidence)
                        boxes = res[0].boxes
                        res_plotted = res[0].plot()[:, :, ::-1]
                        st.image(res_plotted, caption='Gambar Terdeteksi', use_container_width=True)

                        # Display detected waste types prominently
                        st.markdown("---")
                        st.markdown("### ♻️ Jenis Sampah yang Terdeteksi:")
                        
                        if boxes:
                            detected_waste = []
                            for box in boxes:
                                class_id = int(box.cls)
                                class_name = model.names[class_id]
                                conf_value = float(box.conf)
                                detected_waste.append({
                                    'name': class_name,
                                    'confidence': conf_value
                                })
                            
                            # Sort by confidence (highest first)
                            detected_waste.sort(key=lambda x: x['confidence'], reverse=True)
                            
                            # Display each detected waste with color coding
                            for waste in detected_waste:
                                if waste['confidence'] > 0.8:
                                    st.success(f"🟢 **{waste['name'].upper()}** - Kepercayaan: {waste['confidence']:.2f}")
                                elif waste['confidence'] > 0.6:
                                    st.warning(f"🟡 **{waste['name'].upper()}** - Kepercayaan: {waste['confidence']:.2f}")
                                else:
                                    st.info(f"🟠 **{waste['name'].upper()}** - Kepercayaan: {waste['confidence']:.2f}")
                            
                            # Create a sequence from detected waste
                            if len(detected_waste) > 0:
                                sequence = " + ".join([waste['name'].upper() for waste in detected_waste])
                                st.markdown(f"**Urutan Terdeteksi:** {sequence}")
                        else:
                            st.info("🗑️ Tidak ada sampah yang terdeteksi dalam gambar ini")

                        # Save detection result
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                            PIL.Image.fromarray(res_plotted).save(tmpfile.name)
                            with open(tmpfile.name, "rb") as file:
                                detected_image = file.read()
                                helper.save_detection("Image", source_img.name, detected_image)

                        try:
                            with st.expander("📊 Hasil Deteksi Detail"):
                                if boxes:
                                    for i, box in enumerate(boxes):
                                        class_id = int(box.cls)
                                        class_name = model.names[class_id]
                                        conf_value = float(box.conf)
                                        st.write(f"Deteksi {i+1}: **{class_name}** - Kepercayaan: {conf_value:.4f}")
                                else:
                                    st.write("Tidak ada objek yang terdeteksi.")
                        except Exception as ex:
                            st.error("Error memproses hasil deteksi.")
                            st.error(ex)
                    except Exception as ex:
                        st.error("Error menjalankan deteksi.")
                        st.error(ex)

    elif source_radio == settings.WEBCAM:
        # Enhanced webcam with waste detection
        helper.play_webcam_bisindo(confidence, model)

    else:
        st.error("Silakan pilih tipe sumber yang valid!")

# History Page
elif page == "📚 Riwayat":
    st.title("📚 Riwayat Deteksi")
    
    # Add controls for history management
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🗑️ Hapus Semua Riwayat", type="secondary"):
            if st.session_state.get('confirm_delete', False):
                try:
                    # Get all history records first
                    history = helper.get_detection_history()
                    
                    # Delete all records one by one
                    deleted_count = 0
                    for record in history:
                        try:
                            helper.delete_detection_record(record.id)
                            deleted_count += 1
                        except Exception as delete_error:
                            st.warning(f"Gagal menghapus record ID {record.id}: {delete_error}")
                    
                    # Reset confirmation state
                    st.session_state['confirm_delete'] = False
                    
                    # Clear any history-related session state but keep other important states
                    history_keys = [key for key in st.session_state.keys() if 'history' in key.lower() or 'detection' in key.lower()]
                    for key in history_keys:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    if deleted_count > 0:
                        st.success(f"✅ Berhasil menghapus {deleted_count} riwayat!")
                    else:
                        st.info("ℹ️ Tidak ada riwayat yang dihapus.")
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error menghapus semua riwayat: {e}")
                    st.session_state['confirm_delete'] = False
            else:
                st.session_state['confirm_delete'] = True
                st.warning("⚠️ Klik sekali lagi untuk konfirmasi penghapusan semua riwayat")
        
        # Reset confirmation if user doesn't confirm within reasonable time
        if st.session_state.get('confirm_delete', False):
            if st.button("❌ Batal", type="secondary"):
                st.session_state['confirm_delete'] = False
                st.rerun()
    
    try:
        history = helper.get_detection_history()

        if not history:
            st.markdown("""
                <div style='background: linear-gradient(135deg, #E3F2FD, #F3E5F5); 
                           padding: 30px; border-radius: 15px; text-align: center; margin: 20px 0;'>
                    <h3 style='color: #1976D2; margin-bottom: 10px;'>📭 Belum Ada Riwayat Deteksi</h3>
                    <p style='color: #666; margin: 0;'>Mulai deteksi sampah untuk melihat riwayat di sini!</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            # History is already ordered by timestamp desc (latest first) from helper.get_detection_history()
            st.markdown(f"**Total Riwayat:** {len(history)} deteksi")
            
            for i, record in enumerate(history):
                with st.container():
                    # Robust timestamp handling
                    try:
                        if hasattr(record, 'timestamp') and record.timestamp:
                            timestamp_str = record.timestamp.strftime('%d/%m/%Y %H:%M:%S')
                        else:
                            # Fallback: estimate based on record order
                            from datetime import datetime, timedelta
                            estimated_time = datetime.now() - timedelta(minutes=i * 5)
                            timestamp_str = f"{estimated_time.strftime('%d/%m/%Y %H:%M:%S')} (estimasi)"
                    except Exception:
                        # Ultimate fallback
                        timestamp_str = "Tidak tersedia"
                    
                    st.markdown(f"""
                        <div class='detection-result' style='margin-bottom: 20px;'>
                            <h4 style='color: #2E7D32;'>🔍 Deteksi #{i+1}</h4>
                            <p><strong>Sumber:</strong> {record.source_type}</p>
                            <p><strong>File:</strong> {record.source_path}</p>
                            <p><strong>Waktu Deteksi:</strong> {timestamp_str}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Display image with slightly larger, controlled size for better bounding box visibility
                    col1, col2 = st.columns([1.2, 1.8])
                    
                    with col1:
                        try:
                            image_data = base64.b64encode(record.detected_image).decode('utf-8')
                            st.markdown(f'''
                                <img src="data:image/png;base64,{image_data}" 
                                     alt="Hasil Deteksi"
                                     style="width: 100%; max-width: 350px; height: auto; 
                                            border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            ''', unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Error menampilkan gambar: {e}")
                    
                    with col2:
                        st.markdown("### 📊 Detail Deteksi")
                        st.markdown(f"""
                        - **ID Deteksi:** #{record.id}
                        - **Tipe Sumber:** {record.source_type}
                        - **Status:** ✅ Berhasil dideteksi
                        - **Kualitas:** Baik
                        """)
                        
                        # Delete individual record button
                        if st.button(f'🗑️ Hapus Deteksi #{i+1}', key=f'delete_{record.id}'):
                            try:
                                helper.delete_detection_record(record.id)
                                st.success("✅ Riwayat berhasil dihapus!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error menghapus riwayat: {e}")
                    
                    st.markdown("---")
                    
    except Exception as ex:
        st.error("Error saat memuat riwayat deteksi.")
        st.error(ex)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>♻️ <strong>EcoDetect</strong> - Deteksi Sampah Organik dan Anorganik menggunakan YOLOv11</p>
        <p style='font-size: 14px;'>Membantu menciptakan lingkungan yang lebih bersih dan berkelanjutan 🌱</p>
    </div>
""", unsafe_allow_html=True)