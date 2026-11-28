import base64
import datetime
import json
import math
import urllib.request
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="देवभूमि राइड | DevBhoomi Ride",
    page_icon="🚗",
    layout="centered",
)

DB_URL = "https://script.google.com/macros/s/AKfycby3A2XJ0_hrgcs0IRy-pnJzQWmXmwrndsQXZEN73EjNoKKlSIW83dxnjqGp4L6yZ15heQ/exec"

# --- Teal / Slate Theme + बड़े साफ बॉक्स (बिना demo/placeholder के) ---
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #f0fdfa 0%, #ccfbf1 100%);
    }
    .top-brand-card {
        background: linear-gradient(135deg, #0f766e 0%, #115e59 100%);
        color: #ffffff;
        padding: 18px 20px;
        border-radius: 16px;
        margin-bottom: 14px;
        box-shadow: 0 4px 14px rgba(15, 118, 110, 0.22);
    }
    .top-brand-card h2 {
        color: #ffffff !important;
        margin: 0 0 4px 0 !important;
        font-size: 24px !important;
    }
    .top-brand-card p {
        color: #ccfbf1 !important;
        margin: 0 !important;
        font-size: 14px !important;
    }
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        min-height: 56px !important;
        font-size: 18px !important;
        border-radius: 12px !important;
        background-color: #ffffff !important;
    }
    input {
        font-size: 18px !important;
        padding: 12px !important;
    }
    div.stButton > button {
        min-height: 54px !important;
        font-size: 17px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        width: 100% !important;
        background-color: #0f766e !important;
        color: #ffffff !important;
        border: none !important;
    }
    div.stButton > button:hover {
        background-color: #115e59 !important;
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

TEXT = {
    "hi": {
        "brand_title": "🚗 देवभूमि राइड",
        "brand_sub": "उत्तराखंड के लोकल गांव, बाज़ार और चारधाम व पर्यटन रूट्स के लिए",
        "settings_btn": "⚙️ सेटिंग्स",
        "low_net_msg": "📶 नेटवर्क कनेक्शन धीमा हो सकता है — कृपया प्रतीक्षा करें।",
        "choose_lang_label": "भाषा चुनें / Select Language",
        "enter_phone": "मोबाइल नंबर दर्ज करें",
        "enter_email": "ईमेल दर्ज करें",
        "login_next_btn": "➡️ लॉगिन करें / आगे बढ़ें",
        "login_err": "कृपया मोबाइल नंबर और ईमेल दर्ज करें।",
        "create_profile_title": "प्रोफ़ाइल बनाएं (Create Profile)",
        "enter_name": "आपका पूरा नाम दर्ज करें",
        "upload_photo": "प्रोफ़ाइल फ़ोटो जोड़ें / बदलें (वैकल्पिक)",
        "save_profile_btn": "✅ प्रोफ़ाइल सेव करें और आगे बढ़ें",
        "name_err": "कृपया अपना नाम दर्ज करें।",
        "welcome": "नमस्ते",
        "book_trip_btn": "🗺️ अपनी यात्रा बुक करें (Book Your Trip)",
        "my_bookings_btn": "📋 मेरी बुकिंग (My Bookings)",
        "profile_btn": "👤 मेरी प्रोफ़ाइल व फ़ोटो (Profile)",
        "driver_panel_btn": "🚕 ड्राइवर पैनल (Driver Panel)",
        "logout_btn": "🚪 लॉगआउट",
        "main_menu_btn": "🏠 मुख्य मेनू पर जाएं",
        "book_trip_title": "यात्रा बुक करें",
        "step_lbl": "चरण",
        "trip_type_q": "यात्रा का प्रकार चुनें",
        "trip_opt_1": "चारधाम व उत्तराखंड टूरिस्ट / मंदिर रूट",
        "trip_opt_2": "लोकल गांव व बाज़ार राइड",
        "veh_cat_q": "गाड़ी की श्रेणी चुनें",
        "spots_title": "उत्तराखंड के प्रमुख धाम, मंदिर व पर्यटन स्थल",
        "next_from_to": "आगे बढ़ें (From - To चुनें) ➡️",
        "from_q": "कहाँ से जाना है (From)",
        "to_q": "कहाँ जाना है (To)",
        "dist_est": "अनुमानित दूरी: लगभग",
        "dist_note": "नोट: पहाड़ी मोड़, रूट और मौसम के अनुसार वास्तविक दूरी में थोड़ा अंतर आ सकता है।",
        "back_btn": "⬅️ पीछे",
        "next_veh": "आगे बढ़ें (गाड़ी चुनें) ➡️",
        "choose_veh_q": "उपलब्ध गाड़ी चुनें",
        "no_veh_warn": "अभी इस श्रेणी में कोई गाड़ी उपलब्ध नहीं है।",
        "next_confirm": "आगे बढ़ें (पुष्टि करें) ➡️",
        "confirm_title": "बुकिंग पुष्टि करें",
        "passenger_lbl": "यात्री",
        "trip_lbl": "यात्रा प्रकार",
        "route_lbl": "रूट",
        "veh_no_lbl": "गाड़ी नंबर",
        "confirm_booking_btn": "✅ बुकिंग कन्फ़र्म करें",
        "veh_unavail_err": "यह गाड़ी अभी उपलब्ध नहीं है।",
        "booking_sent": "बुकिंग अनुरोध भेज दिया गया है।",
        "waiting_driver": "⏳ ड्राइवर की पुष्टि की प्रतीक्षा है (Waiting for driver confirmation)",
        "driver_lbl": "ड्राइवर",
        "contact_lbl": "संपर्क",
        "new_booking_btn": "➕ नई बुकिंग करें",
        "my_bookings_title": "📋 मेरी बुकिंग",
        "refresh_status_btn": "🔄 स्थिति रिफ्रेश करें",
        "no_booking_found": "इस नंबर पर कोई बुकिंग नहीं मिली।",
        "status_lbl": "स्थिति",
        "profile_title": "👤 मेरी प्रोफ़ाइल",
        "no_photo_cap": "अभी प्रोफ़ाइल फ़ोटो नहीं लगाई गई है।",
        "name_lbl": "नाम",
        "phone_lbl": "मोबाइल नंबर",
        "email_lbl": "ईमेल",
        "rating_lbl": "रेटिंग",
        "rating_note": "यात्रा पूर्ण होने पर रेटिंग अपडेट होगी",
        "driver_panel_title": "🚕 ड्राइवर पैनल",
        "driver_login_btn": "लॉगिन करें",
        "enter_pin": "4-अंकों का पिन दर्ज करें",
        "invalid_pin_err": "मोबाइल नंबर या पिन सही नहीं है।",
        "expired_err": "आपकी आईडी/सदस्यता समाप्त हो गई है।",
        "duty_status_lbl": "ड्यूटी स्थिति बदलें",
        "voice_test_btn": "🔊 आवाज़ अलर्ट चालू / टेस्ट करें",
        "no_active_booking": "अभी कोई सक्रिय बुकिंग नहीं है।",
        "accept_btn": "✅ बुकिंग कन्फ़र्म करें",
        "picked_btn": "🚕 सवारी पिक कर ली (Passenger Picked)",
        "complete_btn": "🏁 राइड पूरी हुई (Trip Completed)",
        "forward_title": "साथी ड्राइवर को बुकिंग भेजें (गाड़ी नंबर दर्ज करें)",
        "forward_btn": "🔁 साथी ड्राइवर को बुकिंग भेजें",
        "settings_title": "⚙️ सेटिंग्स",
        "voice_toggle": "🔔 आवाज़ / नोटिफिकेशन अलर्ट (नई बुकिंग आने पर बोलकर सूचना दें)",
        "low_net_toggle": "📶 कमज़ोर नेटवर्क सूचना मोड",
        "terms_btn": "📜 नियम व शर्तें (Terms)",
        "support_btn": "📞 ग्राहक सहायता (Support)",
        "terms_text": "नियम व शर्तें: देवभूमि राइड स्थानीय व पर्यटन यात्राओं के लिए बुकिंग समन्वय माध्यम है। दूरी पहाड़ी मार्ग के अनुसार अनुमानित होती है। ड्राइवर द्वारा सवारी पिक करते ही गाड़ी On Ride हो जाती है।",
        "support_text": "ग्राहक सहायता: किसी भी बुकिंग या तकनीकी सहायता के लिए संपर्क करें —",
    },
    "en": {
        "brand_title": "🚗 DevBhoomi Ride",
        "brand_sub": "For local Uttarakhand village, market, Char Dham & tourist routes",
        "settings_btn": "⚙️ Settings",
        "low_net_msg": "📶 Network connection may be slow — please wait.",
        "choose_lang_label": "भाषा चुनें / Select Language",
        "enter_phone": "Enter Mobile Number",
        "enter_email": "Enter Email",
        "login_next_btn": "➡️ Login / Continue",
        "login_err": "Please enter mobile number and email.",
        "create_profile_title": "Create Profile",
        "enter_name": "Enter Your Full Name",
        "upload_photo": "Add / Change Profile Photo (Optional)",
        "save_profile_btn": "✅ Save Profile & Continue",
        "name_err": "Please enter your name.",
        "welcome": "Welcome",
        "book_trip_btn": "🗺️ Book Your Trip",
        "my_bookings_btn": "📋 My Bookings",
        "profile_btn": "👤 My Profile & Photo",
        "driver_panel_btn": "🚕 Driver Panel",
        "logout_btn": "🚪 Logout",
        "main_menu_btn": "🏠 Go to Main Menu",
        "book_trip_title": "Book Your Trip",
        "step_lbl": "Step",
        "trip_type_q": "Select Trip Type",
        "trip_opt_1": "Char Dham & Uttarakhand Tourist / Temple Route",
        "trip_opt_2": "Local Village & Market Ride",
        "veh_cat_q": "Select Vehicle Category",
        "spots_title": "Major Shrines, Temples & Tourist Destinations in Uttarakhand",
        "next_from_to": "Next (Select From - To) ➡️",
        "from_q": "Pickup Location (From)",
        "to_q": "Destination (To)",
        "dist_est": "Estimated Distance: approx.",
        "dist_note": "Note: Actual road distance may vary slightly due to mountain turns and weather.",
        "back_btn": "⬅️ Back",
        "next_veh": "Next (Select Vehicle) ➡️",
        "choose_veh_q": "Select Available Vehicle",
        "no_veh_warn": "No vehicle is currently available in this category.",
        "next_confirm": "Next (Confirm) ➡️",
        "confirm_title": "Confirm Booking",
        "passenger_lbl": "Passenger",
        "trip_lbl": "Trip Type",
        "route_lbl": "Route",
        "veh_no_lbl": "Vehicle No",
        "confirm_booking_btn": "✅ Confirm Booking",
        "veh_unavail_err": "This vehicle is no longer available.",
        "booking_sent": "Booking request has been sent.",
        "waiting_driver": "⏳ Waiting for driver confirmation",
        "driver_lbl": "Driver",
        "contact_lbl": "Contact",
        "new_booking_btn": "➕ Make New Booking",
        "my_bookings_title": "📋 My Bookings",
        "refresh_status_btn": "🔄 Refresh Status",
        "no_booking_found": "No bookings found for this mobile number.",
        "status_lbl": "Status",
        "profile_title": "👤 My Profile",
        "no_photo_cap": "No profile photo uploaded yet.",
        "name_lbl": "Name",
        "phone_lbl": "Mobile Number",
        "email_lbl": "Email",
        "rating_lbl": "Rating",
        "rating_note": "Rating updates after trip completion",
        "driver_panel_title": "🚕 Driver Panel",
        "driver_login_btn": "Login",
        "enter_pin": "Enter 4-Digit PIN",
        "invalid_pin_err": "Invalid mobile number or PIN.",
        "expired_err": "Your ID/subscription has expired.",
        "duty_status_lbl": "Change Duty Status",
        "voice_test_btn": "🔊 Enable / Test Voice Alert",
        "no_active_booking": "No active bookings right now.",
        "accept_btn": "✅ Confirm Booking",
        "picked_btn": "🚕 Passenger Picked (Start Ride)",
        "complete_btn": "🏁 Trip Completed",
        "forward_title": "Forward Booking to Partner Driver (Enter Vehicle No)",
        "forward_btn": "🔁 Forward to Partner Driver",
        "settings_title": "⚙️ Settings",
        "voice_toggle": "🔔 Voice / Notification Alert (Speak when new booking arrives)",
        "low_net_toggle": "📶 Low Network Banner Mode",
        "terms_btn": "📜 Terms & Conditions",
        "support_btn": "📞 Customer Support",
        "terms_text": "Terms & Conditions: DevBhoomi Ride coordinates local and tourist cab bookings in Uttarakhand. Distances are estimated for mountain routes. Vehicles switch to On Ride once a passenger is picked up.",
        "support_text": "Customer Support: For any booking or technical help, contact —",
    },
}

LOCATIONS = {
    "ऋषिकेश / Rishikesh": (30.0869, 78.2676),
    "हरिद्वार / Haridwar": (29.9457, 78.1642),
    "देहरादून / Dehradun": (30.3165, 78.0322),
    "उत्तरकाशी / Uttarkashi": (30.7268, 78.4354),
    "हर्षिल घाटी / Harsil Valley": (31.0369, 78.7361),
    "गंगोत्री धाम / Gangotri Dham": (30.9993, 78.9408),
    "यमुनोत्री (जानकी चट्टी) / Yamunotri": (30.9966, 78.4608),
    "केदारनाथ (सोनप्रयाग) / Kedarnath": (30.7352, 79.0669),
    "बद्रीनाथ धाम / Badrinath Dham": (30.7433, 79.4938),
    "जोशीमठ व औली / Joshimath & Auli": (30.5506, 79.5660),
    "चोपता व तुंगनाथ / Chopta & Tungnath": (30.4833, 79.2167),
    "रुद्रप्रयाग / Rudraprayag": (30.2844, 78.9811),
    "श्रीनगर (गढ़वाल) / Srinagar Garhwal": (30.2226, 78.7805),
    "नैनीताल / Nainital": (29.3919, 79.4542),
    "कैंची धाम / Kainchi Dham": (29.4335, 79.5142),
    "भीमताल व सातताल / Bhimtal & Sattal": (29.3446, 79.5632),
    "अल्मोड़ा / Almora": (29.5971, 79.6475),
    "जागेश्वर धाम / Jageshwar Dham": (29.6347, 79.8522),
    "रानीखेत / Ranikhet": (29.6434, 79.4322),
    "कौसानी / Kausani": (29.8453, 79.5961),
    "बागेश्वर व बैजनाथ / Bageshwar & Baijnath": (29.8367, 79.7714),
    "मसूरी / Mussoorie": (30.4598, 78.0644),
    "धनोल्टी / Dhanaulti": (30.4408, 78.2489),
    "चकराता / Chakrata": (30.6976, 77.8648),
    "जिम कॉर्बेट (रामनगर) / Jim Corbett": (29.3952, 78.9122),
    "स्थानीय गांव / बाज़ार / Local Village & Market": (30.1100, 78.2900),
}

HIGHLIGHT_SPOTS = [
    "केदारनाथ / Kedarnath",
    "बद्रीनाथ / Badrinath",
    "गंगोत्री / Gangotri",
    "यमुनोत्री / Yamunotri",
    "कैंची धाम / Kainchi Dham",
    "जागेश्वर धाम / Jageshwar Dham",
    "चोपता व तुंगनाथ / Chopta & Tungnath",
    "जोशीमठ व औली / Joshimath & Auli",
    "नैनीताल / Nainital",
    "मसूरी व धनोल्टी / Mussoorie & Dhanaulti",
    "अल्मोड़ा व रानीखेत / Almora & Ranikhet",
    "उत्तरकाशी व हर्षिल / Uttarkashi & Harsil",
]

FAR_FUTURE = datetime.date(2099, 12, 31)

DEFAULT_DRIVERS = [
    {
        "name": "रमेश रावत / Ramesh Rawat",
        "phone": "9800000001",
        "pin": "1111",
        "vehicle_no": "UK07TA1001",
        "vehicle_name": "Mahindra Bolero",
        "category": "4-Wheeler",
        "route": "Uttarkashi - Gangotri - Rishikesh",
        "status": "Available",
        "plan_type": "Free",
        "expiry_date": "2099-12-31",
        "active": True,
        "rating": "4.8 ★",
        "photo_b64": "",
    },
    {
        "name": "सुरेश नेगी / Suresh Negi",
        "phone": "9800000002",
        "pin": "2222",
        "vehicle_no": "UK10PA2002",
        "vehicle_name": "Maruti WagonR",
        "category": "4-Wheeler",
        "route": "Local Village - Market - Station",
        "status": "Available",
        "plan_type": "Free",
        "expiry_date": "2099-12-31",
        "active": True,
        "rating": "4.7 ★",
        "photo_b64": "",
    },
    {
        "name": "दीपक बिष्ट / Deepak Bisht",
        "phone": "9800000003",
        "pin": "3333",
        "vehicle_no": "UK07S3003",
        "vehicle_name": "Hero Splendor",
        "category": "2-Wheeler",
        "route": "Village to Market Ride",
        "status": "Available",
        "plan_type": "Free",
        "expiry_date": "2099-12-31",
        "active": True,
        "rating": "4.9 ★",
        "photo_b64": "",
    },
]


def sync_to_sheet(payload: dict) -> None:
    if not DB_URL.strip():
        return
    try:
        data = json.dumps(payload, default=str).encode("utf-8")
        req = urllib.request.Request(
            DB_URL.strip(),
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8):
            pass
    except Exception:
        pass


def load_from_sheet() -> None:
    if not DB_URL.strip() or st.session_state.get("sheet_loaded"):
        return
    try:
        sep = "&" if "?" in DB_URL else "?"
        with urllib.request.urlopen(f"{DB_URL.strip()}{sep}action=state", timeout=8) as resp:
            parsed = json.loads(resp.read().decode("utf-8"))
            if isinstance(parsed.get("drivers"), list) and parsed["drivers"]:
                st.session_state.drivers = parsed["drivers"]
            if isinstance(parsed.get("bookings"), list):
                st.session_state.bookings = parsed["bookings"]
    except Exception:
        pass
    st.session_state.sheet_loaded = True


if "lang" not in st.session_state:
    st.session_state.lang = "hi"
if "drivers" not in st.session_state:
    st.session_state.drivers = [dict(d) for d in DEFAULT_DRIVERS]
if "bookings" not in st.session_state:
    st.session_state.bookings = []
if "screen" not in st.session_state:
    st.session_state.screen = "login"
if "trip_substep" not in st.session_state:
    st.session_state.trip_substep = 1
if "passenger_user" not in st.session_state:
    st.session_state.passenger_user = {"name": "", "phone": "", "email": "", "photo_b64": ""}
if "draft_booking" not in st.session_state:
    st.session_state.draft_booking = {
        "trip_type_idx": 0,
        "vehicle_type": "4-Wheeler",
        "pickup": "ऋषिकेश / Rishikesh",
        "drop": "उत्तरकाशी / Uttarkashi",
        "distance_km": 0,
        "driver_vehicle_no": "",
    }
if "settings" not in st.session_state:
    st.session_state.settings = {
        "voice_alert": True,
        "low_network_mode": False,
        "support_phone": "0000000000",
    }
if "logged_in_driver" not in st.session_state:
    st.session_state.logged_in_driver = None
if "show_legal_modal" not in st.session_state:
    st.session_state.show_legal_modal = None

load_from_sheet()
T = TEXT[st.session_state.lang]


def estimate_road_km(pickup_name: str, drop_name: str, hill_multiplier: float = 1.35) -> int:
    if pickup_name == drop_name:
        return 5
    lat1, lon1 = LOCATIONS[pickup_name]
    lat2, lon2 = LOCATIONS[drop_name]
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    straight_km = 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return max(5, round(straight_km * hill_multiplier))


def play_voice_alert(text: str = "देवभूमि राइड पर नई बुकिंग आई है") -> None:
    components.html(
        f"""
        <script>
        try {{
            const u = new SpeechSynthesisUtterance("{text}");
            u.lang = "hi-IN";
            u.rate = 0.95;
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(u);
        }} catch (e) {{}}
        </script>
        """,
        height=0,
    )


def get_driver_by_vehicle(vehicle_no: str):
    clean = vehicle_no.strip().upper().replace(" ", "")
    for d in st.session_state.drivers:
        if str(d.get("vehicle_no", "")).upper().replace(" ", "") == clean:
            return d
    return None


def get_driver_by_phone(phone: str):
    clean = phone.strip()
    for d in st.session_state.drivers:
        if str(d.get("phone", "")).strip() == clean:
            return d
    return None


def is_driver_subscription_valid(driver: dict) -> bool:
    today = datetime.date.today()
    raw_exp = driver.get("expiry_date", FAR_FUTURE)
    if isinstance(raw_exp, datetime.date):
        expiry = raw_exp
    else:
        try:
            expiry = datetime.date.fromisoformat(str(raw_exp)[:10])
        except Exception:
            expiry = FAR_FUTURE
    active_val = driver.get("active", True)
    if isinstance(active_val, str):
        active_val = active_val.strip().lower() not in ["false", "0", "no", "blocked"]
    return bool(active_val) and (today <= expiry)


def persist_state() -> None:
    sync_to_sheet(
        {
            "action": "sync_all",
            "drivers": st.session_state.drivers,
            "bookings": st.session_state.bookings,
        }
    )


# =====================================================================
# FIRST SCREEN: ONLY LANGUAGE SELECT + MOBILE NUMBER + EMAIL + LOGIN
# =====================================================================
if st.session_state.screen == "login":
    st.markdown(
        f"""
        <div class="top-brand-card">
            <h2>{T["brand_title"]}</h2>
            <p>{T["brand_sub"]}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"### {T['choose_lang_label']}")
    lang_choice = st.radio(
        "first_lang_selector",
        ["हिंदी (देवनागरी)", "English"],
        index=0 if st.session_state.lang == "hi" else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    new_lang = "hi" if lang_choice == "हिंदी (देवनागरी)" else "en"
    if new_lang != st.session_state.lang:
        st.session_state.lang = new_lang
        st.rerun()

    st.markdown(f"### {T['enter_phone']}")
    p_phone = st.text_input(
        "login_phone",
        value=st.session_state.passenger_user["phone"],
        placeholder="",
        label_visibility="collapsed",
    )

    st.markdown(f"### {T['enter_email']}")
    p_email = st.text_input(
        "login_email",
        value=st.session_state.passenger_user["email"],
        placeholder="",
        label_visibility="collapsed",
    )

    if st.button(T["login_next_btn"]):
        if not p_phone.strip() or not p_email.strip():
            st.error(T["login_err"])
        else:
            st.session_state.passenger_user["phone"] = p_phone.strip()
            st.session_state.passenger_user["email"] = p_email.strip()
            st.session_state.screen = "create_profile"
            st.rerun()

# =====================================================================
# AFTER LOGIN: TOP BAR + SCREENS
# =====================================================================
else:
    top_left, top_right = st.columns([4, 1])
    with top_left:
        st.markdown(
            f"""
            <div class="top-brand-card">
                <h2>{T["brand_title"]}</h2>
                <p>{T["brand_sub"]}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_right:
        if st.button(T["settings_btn"]):
            st.session_state.screen = "settings"
            st.rerun()

    if st.session_state.settings["low_network_mode"]:
        st.info(T["low_net_msg"])

    # --- CREATE PROFILE ---
    if st.session_state.screen == "create_profile":
        st.subheader(T["create_profile_title"])

        st.markdown(f"### {T['choose_lang_label']}")
        p_lang_choice = st.radio(
            "prof_lang_selector",
            ["हिंदी (देवनागरी)", "English"],
            index=0 if st.session_state.lang == "hi" else 1,
            horizontal=True,
            label_visibility="collapsed",
        )
        new_p_lang = "hi" if p_lang_choice == "हिंदी (देवनागरी)" else "en"
        if new_p_lang != st.session_state.lang:
            st.session_state.lang = new_p_lang
            st.rerun()

        st.markdown(f"### {T['enter_name']}")
        prof_name = st.text_input(
            "prof_name",
            value=st.session_state.passenger_user["name"],
            placeholder="",
            label_visibility="collapsed",
        )

        prof_photo = st.file_uploader(T["upload_photo"], type=["png", "jpg", "jpeg"], key="init_prof_photo")
        if prof_photo is not None:
            st.session_state.passenger_user["photo_b64"] = base64.b64encode(prof_photo.getvalue()).decode("utf-8")

        if st.session_state.passenger_user["photo_b64"]:
            st.image(base64.b64decode(st.session_state.passenger_user["photo_b64"]), width=120)

        if st.button(T["save_profile_btn"]):
            if not prof_name.strip():
                st.error(T["name_err"])
            else:
                st.session_state.passenger_user["name"] = prof_name.strip()
                st.session_state.screen = "home"
                st.rerun()

    # --- HOME MENU ---
    elif st.session_state.screen == "home":
        st.subheader(f"{T['welcome']}, {st.session_state.passenger_user['name'] or 'User'}")

        if st.button(T["book_trip_btn"]):
            st.session_state.trip_substep = 1
            st.session_state.screen = "book_trip"
            st.rerun()

        if st.button(T["my_bookings_btn"]):
            st.session_state.screen = "my_bookings"
            st.rerun()

        if st.button(T["profile_btn"]):
            st.session_state.screen = "profile"
            st.rerun()

        if st.button(T["driver_panel_btn"]):
            st.session_state.screen = "driver_panel"
            st.rerun()

        if st.button(T["logout_btn"]):
            st.session_state.screen = "login"
            st.rerun()

    # --- BOOK YOUR TRIP ---
    elif st.session_state.screen == "book_trip":
        if st.button(T["main_menu_btn"]):
            st.session_state.screen = "home"
            st.rerun()

        sub = st.session_state.trip_substep
        draft = st.session_state.draft_booking
        st.subheader(f"{T['book_trip_title']} — {T['step_lbl']} {min(sub, 4)} / 4")

        if sub == 1:
            st.markdown(f"### {T['trip_type_q']}")
            trip_opts = [T["trip_opt_1"], T["trip_opt_2"]]
            chosen_trip = st.radio(
                "trip_type",
                trip_opts,
                index=draft["trip_type_idx"],
                label_visibility="collapsed",
            )
            draft["trip_type_idx"] = trip_opts.index(chosen_trip)

            st.markdown(f"### {T['veh_cat_q']}")
            draft["vehicle_type"] = st.radio(
                "veh_cat",
                ["4-Wheeler", "2-Wheeler"],
                index=0 if draft["vehicle_type"] == "4-Wheeler" else 1,
                horizontal=True,
                label_visibility="collapsed",
            )

            if draft["trip_type_idx"] == 0:
                st.markdown(f"### {T['spots_title']}")
                st.write(" • ".join(HIGHLIGHT_SPOTS))

            if st.button(T["next_from_to"]):
                st.session_state.trip_substep = 2
                st.rerun()

        elif sub == 2:
            loc_list = list(LOCATIONS.keys())
            st.markdown(f"### {T['from_q']}")
            p_idx = loc_list.index(draft["pickup"]) if draft["pickup"] in loc_list else 0
            draft["pickup"] = st.selectbox("from_loc", loc_list, index=p_idx, label_visibility="collapsed")

            st.markdown(f"### {T['to_q']}")
            d_idx = loc_list.index(draft["drop"]) if draft["drop"] in loc_list else 3
            draft["drop"] = st.selectbox("to_loc", loc_list, index=d_idx, label_visibility="collapsed")

            km = estimate_road_km(draft["pickup"], draft["drop"])
            draft["distance_km"] = km
            st.success(f"📏 {T['dist_est']} **{km} km**")
            st.caption(T["dist_note"])

            c1, c2 = st.columns(2)
            with c1:
                if st.button(T["back_btn"]):
                    st.session_state.trip_substep = 1
                    st.rerun()
            with c2:
                if st.button(T["next_veh"]):
                    st.session_state.trip_substep = 3
                    st.rerun()

        elif sub == 3:
            st.markdown(f"### {T['choose_veh_q']}")
            available_drivers = [
                d
                for d in st.session_state.drivers
                if str(d.get("status", "")).strip() == "Available"
                and str(d.get("category", "")).strip() == draft["vehicle_type"]
                and is_driver_subscription_valid(d)
            ]

            if not available_drivers:
                st.warning(T["no_veh_warn"])
                if st.button(T["back_btn"]):
                    st.session_state.trip_substep = 2
                    st.rerun()
            else:
                options = {
                    f"{d['vehicle_name']} ({d['vehicle_no']}) — {d['name']} ({d.get('rating', '4.8 ★')})": d["vehicle_no"]
                    for d in available_drivers
                }
                selected_label = st.selectbox("avail_vehs", list(options.keys()), label_visibility="collapsed")
                draft["driver_vehicle_no"] = options[selected_label]

                c1, c2 = st.columns(2)
                with c1:
                    if st.button(T["back_btn"]):
                        st.session_state.trip_substep = 2
                        st.rerun()
                with c2:
                    if st.button(T["next_confirm"]):
                        st.session_state.trip_substep = 4
                        st.rerun()

        elif sub == 4:
            trip_label = T["trip_opt_1"] if draft["trip_type_idx"] == 0 else T["trip_opt_2"]
            st.markdown(f"### {T['confirm_title']}")
            st.write(f"**{T['passenger_lbl']}:** {st.session_state.passenger_user['name']} ({st.session_state.passenger_user['phone']})")
            st.write(f"**{T['trip_lbl']}:** {trip_label}")
            st.write(f"**{T['route_lbl']}:** {draft['pickup']} ➔ {draft['drop']} (**~{draft['distance_km']} km**)")
            st.write(f"**{T['veh_no_lbl']}:** {draft['driver_vehicle_no']}")

            c1, c2 = st.columns(2)
            with c1:
                if st.button(T["back_btn"]):
                    st.session_state.trip_substep = 3
                    st.rerun()
            with c2:
                if st.button(T["confirm_booking_btn"]):
                    target = get_driver_by_vehicle(draft["driver_vehicle_no"])
                    if not target or str(target.get("status", "")).strip() != "Available":
                        st.error(T["veh_unavail_err"])
                    else:
                        new_booking = {
                            "id": len(st.session_state.bookings) + 1,
                            "passenger_name": st.session_state.passenger_user["name"],
                            "passenger_phone": st.session_state.passenger_user["phone"],
                            "passenger_email": st.session_state.passenger_user["email"],
                            "trip_type": trip_label,
                            "pickup": draft["pickup"],
                            "drop": draft["drop"],
                            "distance_km": draft["distance_km"],
                            "driver_phone": str(target["phone"]),
                            "driver_name": str(target["name"]),
                            "vehicle_no": str(target["vehicle_no"]),
                            "status": "Waiting for Driver Confirmation",
                            "notice": "",
                        }
                        st.session_state.bookings.append(new_booking)
                        persist_state()
                        st.session_state.trip_substep = 5
                        st.rerun()

        elif sub == 5 and st.session_state.bookings:
            latest = st.session_state.bookings[-1]
            st.success(T["booking_sent"])
            st.info(T["waiting_driver"])
            st.write(f"**{T['route_lbl']}:** {latest['pickup']} ➔ {latest['drop']} (~{latest['distance_km']} km)")
            st.write(f"**{T['driver_lbl']}:** {latest['driver_name']} ({latest['vehicle_no']}) | **{T['contact_lbl']}:** {latest['driver_phone']}")
            if st.button(T["new_booking_btn"]):
                st.session_state.trip_substep = 1
                st.rerun()

    # --- MY BOOKINGS ---
    elif st.session_state.screen == "my_bookings":
        if st.button(T["main_menu_btn"]):
            st.session_state.screen = "home"
            st.rerun()

        st.subheader(T["my_bookings_title"])
        st.markdown(f"### {T['enter_phone']}")
        m_phone = st.text_input(
            "my_booking_phone",
            value=st.session_state.passenger_user["phone"],
            placeholder="",
            label_visibility="collapsed",
        )
        st.session_state.passenger_user["phone"] = m_phone.strip()

        if st.button(T["refresh_status_btn"]):
            st.session_state.sheet_loaded = False
            load_from_sheet()
            st.rerun()

        if m_phone.strip():
            found = [
                b
                for b in reversed(st.session_state.bookings)
                if str(b.get("passenger_phone", "")).strip() == m_phone.strip()
            ]
            if not found:
                st.warning(T["no_booking_found"])
            for b in found:
                st.divider()
                st.markdown(f"**#{b.get('id', '')}** — {b.get('pickup', '')} ➔ {b.get('drop', '')} (~{b.get('distance_km', '')} km)")
                st.info(f"**{T['status_lbl']}:** {b.get('status', '')}")
                if b.get("notice"):
                    st.warning(b["notice"])
                st.write(f"**{T['driver_lbl']}:** {b.get('driver_name', '')} ({b.get('vehicle_no', '')}) | **{T['contact_lbl']}:** {b.get('driver_phone', '')}")

    # --- PROFILE ---
    elif st.session_state.screen == "profile":
        if st.button(T["main_menu_btn"]):
            st.session_state.screen = "home"
            st.rerun()

        st.subheader(T["profile_title"])
        uploaded_photo = st.file_uploader(T["upload_photo"], type=["png", "jpg", "jpeg"], key="prof_page_up")
        if uploaded_photo is not None:
            st.session_state.passenger_user["photo_b64"] = base64.b64encode(uploaded_photo.getvalue()).decode("utf-8")

        if st.session_state.passenger_user["photo_b64"]:
            st.image(base64.b64decode(st.session_state.passenger_user["photo_b64"]), width=140)
        else:
            st.caption(T["no_photo_cap"])

        st.write(f"**{T['name_lbl']}:** {st.session_state.passenger_user['name'] or '—'}")
        st.write(f"**{T['phone_lbl']}:** {st.session_state.passenger_user['phone'] or '—'}")
        st.write(f"**{T['email_lbl']}:** {st.session_state.passenger_user['email'] or '—'}")
        st.write(f"**{T['rating_lbl']}:** 4.8 ★ *({T['rating_note']})*")

    # --- DRIVER PANEL ---
    elif st.session_state.screen == "driver_panel":
        if st.button(T["main_menu_btn"]):
            st.session_state.screen = "home"
            st.rerun()

        st.subheader(T["driver_panel_title"])

        if st.session_state.logged_in_driver is None:
            st.markdown(f"### {T['enter_phone']}")
            l_phone = st.text_input("drv_l_phone", placeholder="", label_visibility="collapsed")
            st.markdown(f"### {T['enter_pin']}")
            l_pin = st.text_input("drv_l_pin", type="password", placeholder="", label_visibility="collapsed")

            if st.button(T["driver_login_btn"]):
                drv = get_driver_by_phone(l_phone)
                if not drv or str(drv.get("pin", "")).strip() != l_pin.strip():
                    st.error(T["invalid_pin_err"])
                elif not is_driver_subscription_valid(drv):
                    st.error(T["expired_err"])
                else:
                    st.session_state.logged_in_driver = str(drv["phone"]).strip()
                    st.rerun()
        else:
            drv = get_driver_by_phone(st.session_state.logged_in_driver)
            if not drv or not is_driver_subscription_valid(drv):
                st.error(T["expired_err"])
                if st.button(T["logout_btn"]):
                    st.session_state.logged_in_driver = None
                    st.rerun()
                st.stop()

            d_photo = st.file_uploader(T["upload_photo"], type=["png", "jpg", "jpeg"], key="drv_photo_up")
            if d_photo is not None:
                drv["photo_b64"] = base64.b64encode(d_photo.getvalue()).decode("utf-8")
                persist_state()

            if drv.get("photo_b64"):
                st.image(base64.b64decode(drv["photo_b64"]), width=140)

            st.markdown(f"### {drv['name']} ({drv['vehicle_no']})")
            st.write(f"**{drv['vehicle_name']}** | **{T['rating_lbl']}:** {drv.get('rating', '4.8 ★')} | **{T['status_lbl']}:** `{drv['status']}`")

            cur_status = str(drv.get("status", "Available")).strip()
            status_list = ["Available", "On Ride", "Off Duty"]
            s_idx = status_list.index(cur_status) if cur_status in status_list else 0
            new_status = st.selectbox(T["duty_status_lbl"], status_list, index=s_idx)
            if new_status != cur_status:
                drv["status"] = new_status
                persist_state()
                st.rerun()

            if st.session_state.settings["voice_alert"]:
                if st.button(T["voice_test_btn"]):
                    play_voice_alert("देवभूमि राइड पर आवाज़ अलर्ट चालू है")

            st.divider()
            my_bookings = [
                b
                for b in st.session_state.bookings
                if str(b.get("driver_phone", "")).strip() == str(drv["phone"]).strip()
                and str(b.get("status", "")).strip() != "Trip Completed"
            ]

            if my_bookings and st.session_state.settings["voice_alert"]:
                play_voice_alert("देवभूमि राइड पर नई बुकिंग आई है")

            if not my_bookings:
                st.caption(T["no_active_booking"])

            for b in my_bookings:
                st.markdown(f"**#{b['id']}** — {b['pickup']} ➔ {b['drop']} (~{b['distance_km']} km)")
                st.write(f"{T['passenger_lbl']}: {b['passenger_name']} | {T['contact_lbl']}: {b['passenger_phone']} | `{b['status']}`")

                if b["status"] == "Waiting for Driver Confirmation":
                    if st.button(T["accept_btn"], key=f"conf_{b['id']}"):
                        b["status"] = "Driver Confirmed"
                        persist_state()
                        st.rerun()

                if b["status"] in ["Waiting for Driver Confirmation", "Driver Confirmed"]:
                    if st.button(T["picked_btn"], key=f"pick_{b['id']}"):
                        b["status"] = "Passenger Picked (On Ride)"
                        drv["status"] = "On Ride"
                        persist_state()
                        st.rerun()

                if b["status"] == "Passenger Picked (On Ride)":
                    if st.button(T["complete_btn"], key=f"done_{b['id']}"):
                        b["status"] = "Trip Completed"
                        drv["status"] = "Available"
                        persist_state()
                        st.rerun()

                st.markdown(f"**{T['forward_title']}**")
                partner_veh = st.text_input("partner_veh", placeholder="", key=f"fwd_veh_{b['id']}", label_visibility="collapsed")
                if st.button(T["forward_btn"], key=f"fwd_btn_{b['id']}"):
                    partner = get_driver_by_vehicle(partner_veh)
                    if not partner:
                        st.error("Vehicle not found / गाड़ी नंबर नहीं मिला।")
                    elif str(partner["phone"]).strip() == str(drv["phone"]).strip():
                        st.error("Enter another partner driver's vehicle number.")
                    elif str(partner.get("status", "")).strip() != "Available" or not is_driver_subscription_valid(partner):
                        st.error("Partner driver is not Available.")
                    else:
                        old_drv_name = drv["name"]
                        b["driver_phone"] = str(partner["phone"])
                        b["driver_name"] = str(partner["name"])
                        b["vehicle_no"] = str(partner["vehicle_no"])
                        b["status"] = "Waiting for Driver Confirmation"
                        b["notice"] = (
                            f"Booking transferred by {old_drv_name}. "
                            f"New driver: {partner['name']} ({partner['vehicle_no']}). Contact: {partner['phone']}"
                        )
                        drv["status"] = "Available"
                        persist_state()
                        st.success(f"Forwarded to {partner['name']} ({partner['vehicle_no']}).")
                        st.rerun()

                st.divider()

            if st.button(T["logout_btn"]):
                st.session_state.logged_in_driver = None
                st.rerun()

    # --- SETTINGS ---
    elif st.session_state.screen == "settings":
        if st.button(T["back_btn"]):
            st.session_state.screen = "home" if st.session_state.passenger_user["name"] else "create_profile"
            st.rerun()

        st.subheader(T["settings_title"])
        st.markdown(f"### {T['choose_lang_label']}")
        s_lang_choice = st.radio(
            "settings_lang",
            ["हिंदी (देवनागरी)", "English"],
            index=0 if st.session_state.lang == "hi" else 1,
            horizontal=True,
            label_visibility="collapsed",
        )
        new_s_lang = "hi" if s_lang_choice == "हिंदी (देवनागरी)" else "en"
        if new_s_lang != st.session_state.lang:
            st.session_state.lang = new_s_lang
            st.rerun()

        st.divider()
        st.session_state.settings["voice_alert"] = st.toggle(
            T["voice_toggle"],
            value=st.session_state.settings["voice_alert"],
        )
        st.session_state.settings["low_network_mode"] = st.toggle(
            T["low_net_toggle"],
            value=st.session_state.settings["low_network_mode"],
        )

    # --- FOOTER (सिर्फ login के बाद वाली screens पर) ---
    st.divider()
    f1, f2 = st.columns(2)
    with f1:
        if st.button(T["terms_btn"]):
            st.session_state.show_legal_modal = "terms" if st.session_state.show_legal_modal != "terms" else None
            st.rerun()
    with f2:
        if st.button(T["support_btn"]):
            st.session_state.show_legal_modal = "support" if st.session_state.show_legal_modal != "support" else None
            st.rerun()

    if st.session_state.show_legal_modal == "terms":
        st.info(T["terms_text"])
    elif st.session_state.show_legal_modal == "support":
        st.info(f"{T['support_text']} **{st.session_state.settings['support_phone']}**")
