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

st.markdown(
    """
    <style>
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        min-height: 56px !important;
        font-size: 18px !important;
        border-radius: 12px !important;
    }
    input {
        font-size: 18px !important;
        padding: 12px !important;
    }
    div.stButton > button {
        min-height: 54px !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

LOCATIONS = {
    "ऋषिकेश": (30.0869, 78.2676),
    "हरिद्वार": (29.9457, 78.1642),
    "देहरादून": (30.3165, 78.0322),
    "उत्तरकाशी": (30.7268, 78.4354),
    "हर्षिल घाटी": (31.0369, 78.7361),
    "गंगोत्री धाम": (30.9993, 78.9408),
    "यमुनोत्री (जानकी चट्टी)": (30.9966, 78.4608),
    "केदारनाथ (सोनप्रयाग / गौरीकुंड)": (30.7352, 79.0669),
    "बद्रीनाथ धाम": (30.7433, 79.4938),
    "जोशीमठ व औली": (30.5506, 79.5660),
    "चोपता व तुंगनाथ मंदिर": (30.4833, 79.2167),
    "रुद्रप्रयाग": (30.2844, 78.9811),
    "श्रीनगर (गढ़वाल)": (30.2226, 78.7805),
    "नैनीताल": (29.3919, 79.4542),
    "कैंची धाम": (29.4335, 79.5142),
    "भीमताल व सातताल": (29.3446, 79.5632),
    "अल्मोड़ा": (29.5971, 79.6475),
    "जागेश्वर धाम": (29.6347, 79.8522),
    "रानीखेत": (29.6434, 79.4322),
    "कौसानी": (29.8453, 79.5961),
    "बागेश्वर व बैजनाथ मंदिर": (29.8367, 79.7714),
    "मसूरी": (30.4598, 78.0644),
    "धनोल्टी": (30.4408, 78.2489),
    "चकराता": (30.6976, 77.8648),
    "जिम कॉर्बेट (रामनगर)": (29.3952, 78.9122),
    "स्थानीय गांव / बाज़ार स्टॉप": (30.1100, 78.2900),
}

HIGHLIGHT_SPOTS = [
    "केदारनाथ (सोनप्रयाग / गौरीकुंड)",
    "बद्रीनाथ धाम",
    "गंगोत्री धाम",
    "यमुनोत्री (जानकी चट्टी)",
    "कैंची धाम",
    "जागेश्वर धाम",
    "चोपता व तुंगनाथ मंदिर",
    "जोशीमठ व औली",
    "नैनीताल",
    "मसूरी व धनोल्टी",
    "अल्मोड़ा व रानीखेत",
    "उत्तरकाशी व हर्षिल घाटी",
]

FAR_FUTURE = datetime.date(2099, 12, 31)

DEFAULT_DRIVERS = [
    {
        "name": "रमेश रावत",
        "phone": "9800000001",
        "pin": "1111",
        "vehicle_no": "UK07TA1001",
        "vehicle_name": "महिंद्रा बोलेरो",
        "category": "4-Wheeler",
        "route": "उत्तरकाशी - गंगोत्री - ऋषिकेश",
        "status": "Available",
        "plan_type": "Free",
        "expiry_date": "2099-12-31",
        "active": True,
    },
    {
        "name": "सुरेश नेगी",
        "phone": "9800000002",
        "pin": "2222",
        "vehicle_no": "UK10PA2002",
        "vehicle_name": "मारुति वैगनआर",
        "category": "4-Wheeler",
        "route": "लोकल गांव - बाज़ार - स्टेशन",
        "status": "Available",
        "plan_type": "Free",
        "expiry_date": "2099-12-31",
        "active": True,
    },
    {
        "name": "दीपक बिष्ट",
        "phone": "9800000003",
        "pin": "3333",
        "vehicle_no": "UK07S3003",
        "vehicle_name": "हीरो स्प्लेंडर",
        "category": "2-Wheeler",
        "route": "गांव से बाज़ार राइड",
        "status": "Available",
        "plan_type": "Free",
        "expiry_date": "2099-12-31",
        "active": True,
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


if "drivers" not in st.session_state:
    st.session_state.drivers = [dict(d) for d in DEFAULT_DRIVERS]
if "bookings" not in st.session_state:
    st.session_state.bookings = []
if "booking_step" not in st.session_state:
    st.session_state.booking_step = 1
if "draft_booking" not in st.session_state:
    st.session_state.draft_booking = {
        "trip_type": "चारधाम व उत्तराखंड टूरिस्ट / मंदिर रूट",
        "vehicle_type": "4-Wheeler",
        "pickup": "ऋषिकेश",
        "drop": "उत्तरकाशी",
        "distance_km": 0,
        "driver_vehicle_no": "",
        "passenger_name": "",
        "passenger_phone": "",
    }
if "settings" not in st.session_state:
    st.session_state.settings = {
        "voice_alert": True,
        "low_network_mode": False,
        "support_phone": "0000000000",
    }
if "logged_in_driver" not in st.session_state:
    st.session_state.logged_in_driver = None

load_from_sheet()


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


if st.session_state.settings["low_network_mode"]:
    st.info("📶 नेटवर्क कनेक्शन धीमा हो सकता है — कृपया प्रतीक्षा करें, आपकी प्रक्रिया जारी है।")

st.title("🚗 देवभूमि राइड")
st.caption("उत्तराखंड के लोकल गांव, बाज़ार और चारधाम व पर्यटन रूट्स के लिए")

mode = st.radio(
    "सेक्शन चुनें",
    ["यात्री बुकिंग", "ड्राइवर पैनल", "सेटिंग्स"],
    horizontal=True,
    label_visibility="collapsed",
)

st.divider()

if mode == "यात्री बुकिंग":
    step = st.session_state.booking_step
    draft = st.session_state.draft_booking

    st.progress(min(step, 4) / 4)
    st.subheader(f"चरण {min(step, 4)} / 4")

    if step == 1:
        st.markdown("### यात्रा का प्रकार चुनें")
        draft["trip_type"] = st.radio(
            "यात्रा प्रकार",
            ["चारधाम व उत्तराखंड टूरिस्ट / मंदिर रूट", "लोकल गांव व बाज़ार राइड"],
            index=0 if "चारधाम" in draft["trip_type"] else 1,
            label_visibility="collapsed",
        )

        st.markdown("### गाड़ी की श्रेणी चुनें")
        draft["vehicle_type"] = st.radio(
            "गाड़ी श्रेणी",
            ["4-Wheeler", "2-Wheeler"],
            index=0 if draft["vehicle_type"] == "4-Wheeler" else 1,
            horizontal=True,
            label_visibility="collapsed",
        )

        if "चारधाम" in draft["trip_type"]:
            st.markdown("### उत्तराखंड के प्रमुख धाम, मंदिर व पर्यटन स्थल")
            st.write(" • ".join(HIGHLIGHT_SPOTS))

        if st.button("आगे बढ़ें (Next) ➡️"):
            st.session_state.booking_step = 2
            st.rerun()

    elif step == 2:
        loc_list = list(LOCATIONS.keys())
        st.markdown("### कहाँ से जाना है")
        p_idx = loc_list.index(draft["pickup"]) if draft["pickup"] in loc_list else 0
        draft["pickup"] = st.selectbox("पिकअप", loc_list, index=p_idx, label_visibility="collapsed")

        st.markdown("### कहाँ जाना है")
        d_idx = loc_list.index(draft["drop"]) if draft["drop"] in loc_list else 3
        draft["drop"] = st.selectbox("गंतव्य", loc_list, index=d_idx, label_visibility="collapsed")

        km = estimate_road_km(draft["pickup"], draft["drop"])
        draft["distance_km"] = km
        st.success(f"📏 अनुमानित दूरी: लगभग **{km} km** *(पहाड़ी मार्ग के अनुसार अनुमानित)*")
        st.caption("नोट: पहाड़ी मोड़, रूट और मौसम के अनुसार वास्तविक दूरी में थोड़ा अंतर आ सकता है।")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ पीछे जाएं"):
                st.session_state.booking_step = 1
                st.rerun()
        with col2:
            if st.button("आगे बढ़ें (Next) ➡️"):
                st.session_state.booking_step = 3
                st.rerun()

    elif step == 3:
        st.markdown("### उपलब्ध गाड़ी चुनें")
        available_drivers = [
            d
            for d in st.session_state.drivers
            if str(d.get("status", "")).strip() == "Available"
            and str(d.get("category", "")).strip() == draft["vehicle_type"]
            and is_driver_subscription_valid(d)
        ]

        if not available_drivers:
            st.warning("अभी इस श्रेणी में कोई गाड़ी उपलब्ध नहीं है। कृपया श्रेणी बदलें या थोड़ी देर बाद प्रयास करें।")
            if st.button("⬅️ पीछे जाएं"):
                st.session_state.booking_step = 2
                st.rerun()
        else:
            options = {
                f"{d['vehicle_name']} ({d['vehicle_no']}) — {d['name']}": d["vehicle_no"]
                for d in available_drivers
            }
            selected_label = st.selectbox("उपलब्ध गाड़ियाँ", list(options.keys()), label_visibility="collapsed")
            draft["driver_vehicle_no"] = options[selected_label]

            col1, col2 = st.columns(2)
            with col1:
                if st.button("⬅️ पीछे जाएं"):
                    st.session_state.booking_step = 2
                    st.rerun()
            with col2:
                if st.button("आगे बढ़ें (Next) ➡️"):
                    st.session_state.booking_step = 4
                    st.rerun()

    elif step == 4:
        st.markdown("### आपका नाम दर्ज करें")
        draft["passenger_name"] = st.text_input(
            "नाम", value=draft["passenger_name"], placeholder="", label_visibility="collapsed"
        )

        st.markdown("### आपका मोबाइल नंबर दर्ज करें")
        draft["passenger_phone"] = st.text_input(
            "मोबाइल नंबर", value=draft["passenger_phone"], placeholder="", label_visibility="collapsed"
        )

        st.markdown("### बुकिंग विवरण जांचें")
        st.write(f"**यात्रा प्रकार:** {draft['trip_type']}")
        st.write(f"**रूट:** {draft['pickup']} ➔ {draft['drop']} (**~{draft['distance_km']} km**)")
        st.write(f"**चयनित गाड़ी नंबर:** {draft['driver_vehicle_no']}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ पीछे जाएं"):
                st.session_state.booking_step = 3
                st.rerun()
        with col2:
            if st.button("✅ बुकिंग कन्फ़र्म करें"):
                if not draft["passenger_name"].strip() or not draft["passenger_phone"].strip():
                    st.error("कृपया अपना नाम और मोबाइल नंबर दर्ज करें।")
                else:
                    target = get_driver_by_vehicle(draft["driver_vehicle_no"])
                    if not target or str(target.get("status", "")).strip() != "Available":
                        st.error("यह गाड़ी अभी उपलब्ध नहीं है। कृपया पीछे जाकर दूसरी गाड़ी चुनें।")
                    else:
                        new_booking = {
                            "id": len(st.session_state.bookings) + 1,
                            "passenger_name": draft["passenger_name"].strip(),
                            "passenger_phone": draft["passenger_phone"].strip(),
                            "trip_type": draft["trip_type"],
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
                        st.session_state.booking_step = 5
                        st.rerun()

    elif step == 5 and st.session_state.bookings:
        latest = st.session_state.bookings[-1]
        st.success("बुकिंग अनुरोध भेज दिया गया है।")
        st.info("⏳ **ड्राइवर की पुष्टि की प्रतीक्षा है (Waiting for driver confirmation)**")
        if latest.get("notice"):
            st.warning(latest["notice"])
        st.write(f"**रूट:** {latest['pickup']} ➔ {latest['drop']} (~{latest['distance_km']} km)")
        st.write(f"**वर्तमान ड्राइवर:** {latest['driver_name']} ({latest['vehicle_no']})")
        st.write(f"**ड्राइवर संपर्क नंबर:** {latest['driver_phone']}")

        if st.button("🔄 स्थिति देखें"):
            st.session_state.sheet_loaded = False
            load_from_sheet()
            st.rerun()
        if st.button("➕ नई बुकिंग करें"):
            st.session_state.booking_step = 1
            st.session_state.draft_booking["driver_vehicle_no"] = ""
            st.rerun()

elif mode == "ड्राइवर पैनल":
    if st.session_state.logged_in_driver is None:
        st.subheader("ड्राइवर लॉगिन")
        st.markdown("### मोबाइल नंबर दर्ज करें")
        login_phone = st.text_input("ड्राइवर नंबर", placeholder="", label_visibility="collapsed")

        st.markdown("### 4-अंकों का पिन दर्ज करें")
        login_pin = st.text_input("पिन", type="password", placeholder="", label_visibility="collapsed")

        if st.button("लॉगिन करें"):
            drv = get_driver_by_phone(login_phone)
            if not drv or str(drv.get("pin", "")).strip() != login_pin.strip():
                st.error("मोबाइल नंबर या पिन सही नहीं है।")
            elif not is_driver_subscription_valid(drv):
                st.error("आपकी आईडी/सदस्यता समाप्त हो गई है। कृपया एडमिन से संपर्क करें।")
            else:
                st.session_state.logged_in_driver = str(drv["phone"]).strip()
                st.rerun()
    else:
        drv = get_driver_by_phone(st.session_state.logged_in_driver)
        if not drv or not is_driver_subscription_valid(drv):
            st.error("आपकी आईडी ब्लॉक या समाप्त हो गई है।")
            if st.button("लॉगआउट"):
                st.session_state.logged_in_driver = None
                st.rerun()
            st.stop()

        st.subheader(f"नमस्ते, {drv['name']} ({drv['vehicle_no']})")
        st.write(f"**गाड़ी का नाम:** {drv['vehicle_name']} | **वर्तमान स्थिति:** `{drv['status']}`")

        cur_status = str(drv.get("status", "Available")).strip()
        status_list = ["Available", "On Ride", "Off Duty"]
        s_idx = status_list.index(cur_status) if cur_status in status_list else 0
        new_status = st.selectbox("ड्यूटी स्थिति बदलें", status_list, index=s_idx)
        if new_status != cur_status:
            drv["status"] = new_status
            persist_state()
            st.rerun()

        if st.session_state.settings["voice_alert"]:
            if st.button("🔊 आवाज़ अलर्ट चालू / टेस्ट करें"):
                play_voice_alert("देवभूमि राइड पर आवाज़ अलर्ट चालू है")

        st.divider()
        st.subheader("आने वाली व सक्रिय बुकिंग्स")

        my_bookings = [
            b
            for b in st.session_state.bookings
            if str(b.get("driver_phone", "")).strip() == str(drv["phone"]).strip()
            and str(b.get("status", "")).strip() != "Trip Completed"
        ]

        if my_bookings and st.session_state.settings["voice_alert"]:
            play_voice_alert("देवभूमि राइड पर नई बुकिंग आई है")

        if not my_bookings:
            st.caption("अभी कोई सक्रिय बुकिंग नहीं है।")

        for b in my_bookings:
            st.markdown(f"**बुकिंग #{b['id']}** — {b['pickup']} ➔ {b['drop']} (~{b['distance_km']} km)")
            st.write(f"यात्री: {b['passenger_name']} | संपर्क: {b['passenger_phone']} | स्थिति: `{b['status']}`")

            if b["status"] == "Waiting for Driver Confirmation":
                if st.button("✅ बुकिंग कन्फ़र्म करें", key=f"conf_{b['id']}"):
                    b["status"] = "Driver Confirmed"
                    persist_state()
                    st.rerun()

            if b["status"] in ["Waiting for Driver Confirmation", "Driver Confirmed"]:
                if st.button("🚕 सवारी पिक कर ली (Passenger Picked)", key=f"pick_{b['id']}"):
                    b["status"] = "Passenger Picked (On Ride)"
                    drv["status"] = "On Ride"
                    persist_state()
                    st.rerun()

            if b["status"] == "Passenger Picked (On Ride)":
                if st.button("🏁 राइड पूरी हुई (Trip Completed)", key=f"done_{b['id']}"):
                    b["status"] = "Trip Completed"
                    drv["status"] = "Available"
                    persist_state()
                    st.rerun()

            st.markdown("**साथी ड्राइवर को बुकिंग भेजें (गाड़ी नंबर दर्ज करें)**")
            partner_veh = st.text_input(
                "साथी गाड़ी नंबर",
                placeholder="",
                key=f"fwd_veh_{b['id']}",
                label_visibility="collapsed",
            )
            if st.button("🔁 साथी ड्राइवर को बुकिंग भेजें", key=f"fwd_btn_{b['id']}"):
                partner = get_driver_by_vehicle(partner_veh)
                if not partner:
                    st.error("यह गाड़ी नंबर सिस्टम में नहीं मिला।")
                elif str(partner["phone"]).strip() == str(drv["phone"]).strip():
                    st.error("कृपया किसी अन्य साथी ड्राइवर की गाड़ी नंबर दर्ज करें।")
                elif str(partner.get("status", "")).strip() != "Available" or not is_driver_subscription_valid(partner):
                    st.error("यह साथी ड्राइवर अभी Available नहीं है या उसकी आईडी सक्रिय नहीं है।")
                else:
                    old_drv_name = drv["name"]
                    b["driver_phone"] = str(partner["phone"])
                    b["driver_name"] = str(partner["name"])
                    b["vehicle_no"] = str(partner["vehicle_no"])
                    b["status"] = "Waiting for Driver Confirmation"
                    b["notice"] = (
                        f"बुकिंग {old_drv_name} द्वारा साथी ड्राइवर को ट्रांसफर की गई है। "
                        f"अब आपके ड्राइवर {partner['name']} ({partner['vehicle_no']}) हैं। "
                        f"कृपया अभी संपर्क करें: {partner['phone']}"
                    )
                    drv["status"] = "Available"
                    persist_state()
                    st.success(f"बुकिंग {partner['name']} ({partner['vehicle_no']}) को भेज दी गई है।")
                    st.rerun()

            st.divider()

        if st.button("लॉगआउट करें"):
            st.session_state.logged_in_driver = None
            st.rerun()

elif mode == "सेटिंग्स":
    st.subheader("⚙️ सेटिंग्स")

    st.session_state.settings["voice_alert"] = st.toggle(
        "🔊 आवाज़ अलर्ट (नई बुकिंग आने पर बोलकर सूचना दें)",
        value=st.session_state.settings["voice_alert"],
    )

    st.session_state.settings["low_network_mode"] = st.toggle(
        "📶 कमज़ोर नेटवर्क सूचना मोड (Low Network Banner)",
        value=st.session_state.settings["low_network_mode"],
    )

    st.divider()
    st.markdown("### सहायता व जानकारी")
    st.write(f"सहायता संपर्क नंबर: {st.session_state.settings['support_phone']}")
    st.caption("नोट: फ़ोन लॉक होने पर भी तेज़ नोटिफिकेशन अलर्ट के लिए Android नोटिफिकेशन साउंड/ntfy का उपयोग करें।")
