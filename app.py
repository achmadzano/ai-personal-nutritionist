import streamlit as st
from PIL import Image
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import hashlib
import time

from database import DatabaseManager
from ai_analyzer import NutritionAnalyzer

# Page config
st.set_page_config(
    page_title="AI Personal Nutritionist",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database and AI analyzer
@st.cache_resource
def init_services():
    db = DatabaseManager()
    analyzer = NutritionAnalyzer()
    return db, analyzer

db, analyzer = init_services()

# Session persistence using query parameters and localStorage
def create_persistent_session(username, user_data):
    """Create a persistent session that survives refresh"""
    # Save to session state
    st.session_state.logged_in = True
    st.session_state.username = username
    st.session_state.user_data = user_data
    
    # Set query parameters for session persistence
    st.query_params.session_active = "true"
    st.query_params.u = username

def check_persistent_session():
    """Check if there's a valid persistent session"""
    if "session_active" in st.query_params and "u" in st.query_params:
        username = st.query_params.u
        
        # Verify user exists in database
        try:
            user_data = db.users.find_one({"username": username})
            if user_data:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.user_data = user_data
                return True
        except:
            pass
    
    return False

def clear_persistent_session():
    """Clear persistent session"""
    # Clear session state
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_data = None
    
    # Clear query parameters
    if "session_active" in st.query_params:
        del st.query_params.session_active
    if "u" in st.query_params:
        del st.query_params.u

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'session_checked' not in st.session_state:
    st.session_state.session_checked = False

# Check for persistent session on app start
if not st.session_state.logged_in and not st.session_state.session_checked:
    check_persistent_session()
    st.session_state.session_checked = True

def login_page():
    """Login page UI"""
    st.title("🥗 AI Personal Nutritionist")
    st.subheader("Masuk ke Akun Anda")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Add "Remember Me" checkbox
        remember_me = st.checkbox("Ingat saya", value=True, help="Session akan tersimpan saat refresh halaman")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Masuk", use_container_width=True)
            
            if submit:
                if username and password:
                    success, user_data = db.authenticate_user(username, password)
                    if success:
                        if remember_me:
                            # Create persistent session
                            create_persistent_session(username, user_data)
                        else:
                            # Regular session (will be lost on refresh)
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.user_data = user_data
                        
                        st.success("Login berhasil!")
                        st.rerun()
                    else:
                        st.error("Username atau password salah!")
                else:
                    st.error("Mohon isi username dan password!")
        
        st.divider()
        
        if st.button("Belum punya akun? Daftar di sini", use_container_width=True):
            st.session_state.show_register = True
            st.rerun()

def register_page():
    """Registration page UI"""
    st.title("🥗 AI Personal Nutritionist")
    st.subheader("Daftar Akun Baru")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("register_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Konfirmasi Password", type="password")
            submit = st.form_submit_button("Daftar", use_container_width=True)
            
            if submit:
                if username and email and password and confirm_password:
                    if password == confirm_password:
                        success, message = db.create_user(username, email, password)
                        if success:
                            st.success("Akun berhasil dibuat! Silakan login.")
                            st.session_state.show_register = False
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Password tidak cocok!")
                else:
                    st.error("Mohon isi semua field!")
        
        st.divider()
        
        if st.button("Sudah punya akun? Login di sini", use_container_width=True):
            st.session_state.show_register = False
            st.rerun()

def display_nutrition_results(analysis_result):
    """Display nutrition analysis results"""
    if "error" in analysis_result:
        st.error(f"Error dalam analisis: {analysis_result['error']}")
        if "raw_response" in analysis_result:
            st.text_area("Raw Response:", analysis_result["raw_response"], height=200)
        return
    
    # Display detected foods
    if "foods_detected" in analysis_result:
        st.subheader("🍽️ Makanan yang Terdeteksi")
        foods = ", ".join(analysis_result["foods_detected"])
        st.write(f"**{foods}**")
    
    # Display total calories
    if "total_calories" in analysis_result:
        col1, col2, col3 = st.columns(3)
        with col2:
            st.metric(
                label="Total Kalori",
                value=f"{analysis_result['total_calories']} kcal" if isinstance(analysis_result['total_calories'], (int, float)) else str(analysis_result['total_calories'])
            )
    
    # Display nutritional breakdown
    if "nutritional_breakdown" in analysis_result:
        st.subheader("📊 Breakdown Nutrisi")
        breakdown = analysis_result["nutritional_breakdown"]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Protein", breakdown.get("protein", "N/A"))
        with col2:
            st.metric("Karbohidrat", breakdown.get("carbohydrates", "N/A"))
        with col3:
            st.metric("Lemak", breakdown.get("fat", "N/A"))
        with col4:
            st.metric("Serat", breakdown.get("fiber", "N/A"))
        
        # Create pie chart for macronutrients
        if all(key in breakdown for key in ["protein", "carbohydrates", "fat"]):
            try:
                protein_val = float(breakdown["protein"].replace("g", "")) * 4  # 4 kcal/g
                carb_val = float(breakdown["carbohydrates"].replace("g", "")) * 4  # 4 kcal/g
                fat_val = float(breakdown["fat"].replace("g", "")) * 9  # 9 kcal/g
                
                fig = px.pie(
                    values=[protein_val, carb_val, fat_val],
                    names=["Protein", "Karbohidrat", "Lemak"],
                    title="Distribusi Makronutrien (berdasarkan kalori)"
                )
                st.plotly_chart(fig, use_container_width=True)
            except:
                pass
    
    # Display individual foods
    if "individual_foods" in analysis_result:
        st.subheader("🥘 Detail per Makanan")
        for food in analysis_result["individual_foods"]:
            with st.expander(f"{food.get('name', 'Unknown Food')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Porsi:** {food.get('estimated_portion', 'N/A')}")
                    st.write(f"**Kalori:** {food.get('calories', 'N/A')} kcal")
                with col2:
                    st.write(f"**Protein:** {food.get('protein', 'N/A')}")
                    st.write(f"**Karbohidrat:** {food.get('carbs', 'N/A')}")
                    st.write(f"**Lemak:** {food.get('fat', 'N/A')}")
    
    # Display health tips
    if "health_tips" in analysis_result:
        st.subheader("💡 Tips Kesehatan")
        for tip in analysis_result["health_tips"]:
            st.write(f"• {tip}")
    
    # Display confidence score
    if "confidence_score" in analysis_result:
        st.subheader("🎯 Akurasi Analisis")
        confidence = analysis_result["confidence_score"]
        st.progress(confidence)
        st.write(f"Tingkat kepercayaan: {confidence*100:.1f}%")

def main_app():
    """Main application UI for logged-in users"""
    # Sidebar
    with st.sidebar:
        st.title(f"👋 Halo, {st.session_state.username}!")
        
        menu = st.selectbox(
            "Menu",
            ["🏠 Beranda", "📱 Analisis Makanan", "📊 Riwayat", "👤 Profil"]
        )
        
        st.divider()
        
        if st.button("🚪 Logout", use_container_width=True):
            clear_persistent_session()
            st.success("Berhasil logout!")
            st.rerun()
    
    # Main content
    if menu == "🏠 Beranda":
        st.title("🥗 AI Personal Nutritionist")
        st.write("Selamat datang di aplikasi AI Personal Nutritionist! Upload foto makanan Anda untuk mendapatkan analisis nutrisi yang akurat.")
        
        # Quick stats
        logs = db.get_user_logs(st.session_state.username, limit=5)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Analisis", len(logs))
        with col2:
            # Calculate average calories from recent logs
            avg_calories = 0
            valid_logs = 0
            for log in logs:
                if "analysis_result" in log and "total_calories" in log["analysis_result"]:
                    try:
                        calories = log["analysis_result"]["total_calories"]
                        if isinstance(calories, (int, float)):
                            avg_calories += calories
                            valid_logs += 1
                    except:
                        pass
            
            if valid_logs > 0:
                avg_calories = avg_calories / valid_logs
                st.metric("Rata-rata Kalori", f"{avg_calories:.0f} kcal")
            else:
                st.metric("Rata-rata Kalori", "N/A")
        
        with col3:
            st.metric("Analisis Hari Ini", len([log for log in logs if log["timestamp"].date() == datetime.now().date()]))
        
        # --- EVALUASI KALORI HARIAN ---
        st.divider()
        st.subheader("Evaluasi Nutrisi Harian")
        user_profile = db.get_user_profile(st.session_state.username)
        if user_profile:
            from datetime import date
            today = date.today().isoformat()
            daily_meals = db.get_daily_meals(st.session_state.username, today)
            meal_types = [meal.get('meal_type') for meal in daily_meals]
            total_cal = sum([meal.get('analysis_result', {}).get('total_calories', 0) for meal in daily_meals])
            daily_need = db.calculate_daily_calorie_needs(user_profile)
            missing_meals = []
            for m in ['breakfast','lunch','dinner']:
                if m not in meal_types:
                    missing_meals.append(m)
            meal_map = {'breakfast':'Sarapan','lunch':'Makan Siang','dinner':'Makan Malam'}
            if missing_meals:
                st.warning(f"Belum ada data untuk: {', '.join([meal_map[m] for m in missing_meals])}")
            st.write(f"**Total kalori hari ini:** {total_cal} kcal dari kebutuhan {daily_need} kcal")
            # Tampilkan detail makanan harian
            if daily_meals:
                st.markdown("### Makanan Hari Ini")
                # Hitung kebutuhan protein harian (standar: 1.2 gram x berat badan)
                protein_target = round(user_profile['current_weight'] * 1.2)
                total_protein = 0
                for meal in daily_meals:
                    meal_label = meal_map.get(meal.get('meal_type'), meal.get('meal_type').capitalize())
                    result = meal.get('analysis_result', {})
                    foods = ', '.join(result.get('foods_detected', []))
                    cal = result.get('total_calories', 0)
                    protein = result.get('nutritional_breakdown', {}).get('protein', 0)
                    # Ambil nilai protein numerik
                    if isinstance(protein, str) and protein.endswith('g'):
                        try:
                            protein_num = float(protein.replace('g','').strip())
                        except:
                            protein_num = 0
                        protein_val = protein
                    else:
                        protein_num = float(protein)
                        protein_val = f"{protein}g"
                    total_protein += protein_num
                    # Saran berdasarkan BMI
                    bmi = db.calculate_bmi(user_profile['current_weight'], user_profile['height'])
                    bmi_cat, _ = db.get_bmi_category(bmi)
                    bmi_note = ""
                    if bmi_cat == "Underweight":
                        bmi_note = "(Disarankan pilih makanan lebih padat kalori/protein)"
                    elif bmi_cat == "Overweight" or bmi_cat == "Obese":
                        bmi_note = "(Pilih makanan rendah kalori/lemak, perbanyak sayur)"
                    elif bmi_cat == "Normal":
                        bmi_note = "(Pertahankan pola makan seimbang)"
                    st.write(f"- **{meal_label}:** {foods} (**{cal} kcal, {protein_val} protein**) {bmi_note}")
                # Saran protein harian
                st.write(f"**Total protein hari ini:** {total_protein:.1f}g dari target {protein_target}g")
                if total_protein < protein_target * 0.9:
                    st.info(f"Asupan protein hari ini kurang dari kebutuhan. Tambahkan sumber protein seperti telur, ayam, ikan, tahu, tempe.")
                elif total_protein > protein_target * 1.2:
                    st.warning(f"Asupan protein melebihi kebutuhan harian. Tidak masalah jika aktif, tapi perhatikan keseimbangan nutrisi.")
                else:
                    st.success("Asupan protein harian sudah sesuai target!")
            # Saran kalori
            if total_cal < daily_need - 100:
                st.info(f"Asupan kalori hari ini kurang {daily_need-total_cal} kcal dari target. Tambahkan porsi makan atau pilih makanan lebih padat kalori.")
            elif total_cal > daily_need + 100:
                st.warning(f"Asupan kalori hari ini melebihi target {total_cal-daily_need} kcal. Kurangi porsi atau pilih makanan lebih sehat besok.")
            else:
                st.success("Asupan kalori hari ini sudah sesuai target! Pertahankan pola makan ini.")
            # Status BMI
            bmi = db.calculate_bmi(user_profile['current_weight'], user_profile['height'])
            bmi_cat, bmi_icon = db.get_bmi_category(bmi)
            st.write(f"**Status BMI:** {bmi} {bmi_icon} ({bmi_cat})")
        else:
            st.info("Lengkapi profil tubuh Anda di menu Profil untuk mendapatkan evaluasi nutrisi harian.")
    
    elif menu == "📱 Analisis Makanan":
        st.title("📱 Analisis Makanan")
        st.write("Upload foto makanan untuk mendapatkan analisis nutrisi lengkap")
        
        uploaded_file = st.file_uploader(
            "Pilih foto makanan",
            type=["jpg", "jpeg", "png"],
            help="Format yang didukung: JPG, JPEG, PNG"
        )
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            col1, col2 = st.columns([1, 1])
            with col1:
                st.subheader("🖼️ Foto yang Diupload")
                st.image(image, caption="Foto makanan Anda", use_container_width=True)
            with col2:
                st.subheader("🤖 Analisis AI")
                meal_type = st.selectbox(
                    "Jenis Makan",
                    ["Sarapan", "Makan Siang", "Makan Malam"],
                    key="meal_type_select"
                )
                meal_type_map = {"Sarapan": "breakfast", "Makan Siang": "lunch", "Makan Malam": "dinner"}
                if st.button("🔍 Analisis & Simpan", use_container_width=True):
                    with st.spinner("Menganalisis foto makanan..."):
                        analysis_result = analyzer.analyze_food(image)
                        image_data = uploaded_file.getvalue()
                        # Simpan ke log umum
                        db.save_nutrition_log(
                            st.session_state.username,
                            image_data,
                            analysis_result
                        )
                        # Simpan ke log harian (sarapan/lunch/dinner)
                        db.save_daily_meal(
                            st.session_state.username,
                            meal_type_map[meal_type],
                            image_data,
                            analysis_result
                        )
                        st.success(f"Analisis selesai & disimpan sebagai {meal_type}!")
            # Tampilkan hasil jika sudah dianalisis
            if 'analysis_result' in locals():
                st.divider()
                display_nutrition_results(analysis_result)
    
    elif menu == "📊 Riwayat":
        st.title("📊 Riwayat Analisis")
        
        logs = db.get_user_logs(st.session_state.username, limit=20)
        
        if logs:
            st.write(f"Menampilkan {len(logs)} analisis terakhir")
            
            for i, log in enumerate(logs):
                with st.expander(f"Analisis {i+1} - {log['timestamp'].strftime('%d/%m/%Y %H:%M')}"):
                    if "analysis_result" in log:
                        display_nutrition_results(log["analysis_result"])
        else:
            st.info("Belum ada riwayat analisis. Mulai dengan mengupload foto makanan!")
    
    elif menu == "👤 Profil":
        st.title("👤 Profil Pengguna")
        
        user_info = st.session_state.user_data
        # Ambil profil user dari database
        user_profile = db.get_user_profile(st.session_state.username)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Informasi Akun")
            st.write(f"**Username:** {user_info.get('username', 'N/A')}")
            st.write(f"**Email:** {user_info.get('email', 'N/A')}")
            st.write(f"**Bergabung:** {user_info.get('created_at', 'N/A').strftime('%d/%m/%Y') if user_info.get('created_at') else 'N/A'}")
        with col2:
            st.subheader("Statistik")
            total_logs = len(db.get_user_logs(st.session_state.username, limit=1000))
            st.write(f"**Total Analisis:** {total_logs}")
        st.divider()
        
        # Form profil tubuh
        st.subheader("Profil Tubuh & Target")
        if user_profile:
            default_height = user_profile.get('height', 170)
            default_weight = user_profile.get('current_weight', 65)
            default_target = user_profile.get('target_weight', 65)
            default_age = user_profile.get('age', 25)
            default_gender = user_profile.get('gender', 'male')
            default_activity = user_profile.get('activity_level', 'sedentary')
        else:
            default_height = 170
            default_weight = 65
            default_target = 65
            default_age = 25
            default_gender = 'male'
            default_activity = 'sedentary'
        with st.form("profile_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                height = st.number_input("Tinggi Badan (cm)", min_value=100, max_value=250, value=default_height)
                age = st.number_input("Usia", min_value=10, max_value=100, value=default_age)
            with col2:
                current_weight = st.number_input("Berat Sekarang (kg)", min_value=30, max_value=200, value=default_weight)
                target_weight = st.number_input("Target Berat (kg)", min_value=30, max_value=200, value=default_target)
            with col3:
                gender = st.selectbox("Jenis Kelamin", ["male", "female"], index=0 if default_gender=="male" else 1)
                activity_level = st.selectbox(
                    "Aktivitas Harian",
                    [
                        ("sedentary", "Sangat ringan (banyak duduk)"),
                        ("light", "Ringan (jalan kaki, sedikit olahraga)"),
                        ("moderate", "Sedang (olahraga 3-5x/minggu)"),
                        ("active", "Aktif (kerja fisik/olahraga berat)"),
                        ("very_active", "Sangat aktif (atlet, kerja fisik berat)")
                    ],
                    format_func=lambda x: x[1],
                    index=[a[0] for a in [
                        ("sedentary", "Sangat ringan (banyak duduk)"),
                        ("light", "Ringan (jalan kaki, sedikit olahraga)"),
                        ("moderate", "Sedang (olahraga 3-5x/minggu)"),
                        ("active", "Aktif (kerja fisik/olahraga berat)"),
                        ("very_active", "Sangat aktif (atlet, kerja fisik berat)")
                    ]].index(default_activity)
                )
                activity_level = activity_level[0]
            submit = st.form_submit_button("Simpan/Update Profil", use_container_width=True)
            if submit:
                ok = db.save_user_profile(
                    st.session_state.username,
                    height,
                    current_weight,
                    target_weight,
                    age,
                    gender,
                    activity_level
                )
                if ok:
                    st.success("Profil berhasil disimpan!")
                else:
                    st.error("Gagal menyimpan profil.")
        
        # Tampilkan ringkasan BMI dan kalori
        if user_profile or submit:
            if not user_profile or submit:
                # Ambil data terbaru
                user_profile = db.get_user_profile(st.session_state.username)
            bmi = db.calculate_bmi(user_profile['current_weight'], user_profile['height'])
            bmi_cat, bmi_icon = db.get_bmi_category(bmi)
            min_w, max_w = db.calculate_ideal_weight_range(user_profile['height'])
            daily_cal = db.calculate_daily_calorie_needs(user_profile)
            st.info(f"**BMI:** {bmi} {bmi_icon} ({bmi_cat})\n\nBerat ideal: {min_w} - {max_w} kg\n\nKebutuhan kalori harian: {daily_cal} kcal\n\nTarget berat: {user_profile['target_weight']} kg")

# Main app logic
def main():
    # Check if we should show register page
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    
    if not st.session_state.logged_in:
        if st.session_state.show_register:
            register_page()
        else:
            login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()