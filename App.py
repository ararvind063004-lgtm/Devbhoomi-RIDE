import streamlit as st
import requests
import math
from urllib.parse import quote

st.set_page_config(page_title="DevBhoomi Ride", page_icon="🏔️", layout="centered")

# --- FREE UTTARAKHAND VILLAGE SEARCH (OPENSTREETMAP PHOTON API) ---
@st.cache_data(ttl=3600)
def search_uk_village(query):
    if not query or len(query.strip()) < 3:
        return []
    try:
        url = "https://photon.komoot.io/api/"
        params = {"q": f"{query.strip()} Uttarakhand India", "limit": 6}
        res = requests.get(url, params=params, headers={"User-Agent": "DevBhoomiRide/1.0"}, timeout=5)
        if res.status_code == 200:
            features = res.json().get("features", [])
            results = []
            seen = set()
            for f in features:
                props = f.get("properties", {})
                coords = f.get("geometry", {}).get("coordinates", [None, None])
                name = props.get("name", "")
                district = props.get("county") or props.get("city") or props.get("state_district") or ""
                state = props.get("state", "")
                if name and ("Uttarakhand" in state or "India" in props.get("country", "")):
                    label = f"{name}, {district}" if district and district != name else name
                    if label not in seen:
                        seen.add(label)
                        results.append({"label": label, "name": name, "lat": coords[1], "lon": coords[0]})
            return results
    except Exception:
        return []
    return []

def haversine_km(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return 9999
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# --- LANGUAGE SWITCH ---
lang = st.radio("🌐 भाषा चुनें / Language:", ["हिंदी", "English"], horizontal=True)
is_hi = (lang == "हिंदी")

# --- REGISTERED DRIVERS DATA (DEMO) ---
if "drivers" not in st.session_state:
    st.session_state.drivers = {
        "9876543210": {
            "name": "रमेश बिष्ट",
            "phone": "9876543210",
            "address": "हल्द्वानी, नैनीताल",
            "vehicle_type": "Cab / Shared",
            "vehicle": "Mahindra Bolero (UK 04 TA 4521)",
            "license": "UK0420180012345",
            "reg_paid": True
        }
    }

if "logged_in_driver" not in st.session_state:
    st.session_state.logged_in_driver = None

# --- INITIAL DEMO TRIPS ---
if "trips" not in st.session_state:
    st.session_state.trips = [
        {
            "id": 1, "driver": "रमेश बिष्ट", "phone": "9876543210",
            "vehicle_type": "Cab / Shared", "vehicle": "Mahindra Bolero (UK 04 TA 4521)",
            "stops": ["Haldwani", "Kathgodam", "Bhimtal", "Bhowali", "Kainchi Dham", "Almora"],
            "lat": 29.2183, "lon": 79.5130,
            "time": "08:30 AM", "full_fare": 250, "current_stop_idx": 1,
            "delay_mins": 10, "delay_reason": "काठगोदाम में सवारी बैठा रहे हैं",
            "status": "Active",
            "seats": {
                "Front-1": "Booked", "Mid-1": "Booked", "Mid-2": "Booked",
                "Mid-3": "Booked", "Back-1": "Booked", "Back-2": "Booked", "Back-3": "Available"
            }
        },
        {
            "id": 2, "driver": "अमित रावत", "phone": "9756001122",
            "vehicle_type": "Bike / Scooty", "vehicle": "Honda Activa (UK 04 AB 2233)",
            "stops": ["Haldwani", "Kathgodam", "Bhimtal", "Bhowali"],
            "lat": 29.3461, "lon": 79.5519,
            "time": "अभी उपलब्ध", "full_fare": 80, "current_stop_idx": 0,
            "delay_mins": 0, "delay_reason": "समय पर", "status": "Active",
            "seats": {"Pillion-Seat": "Available"}
        }
    ]

if "bookings" not in st.session_state:
    st.session_state.bookings = []

active_trips = [t for t in st.session_state.trips if t["status"] == "Active"]

# --- HEADER ---
st.title("🏔️ देवभूमि राइड" if is_hi else "🏔️ DevBhoomi Ride")
st.caption("उत्तराखंड के हर गाँव से बाज़ार तक — टैक्सी, बाइक और स्कूटी" if is_hi else "From every Uttarakhand village to city — Cab, Bike & Scooty")

t1, t2, t3 = st.tabs([
    "🔍 सीट बुक करें" if is_hi else "🔍 Book Ride",
    "📍 लाइव लोकेशन" if is_hi else "📍 Live Track",
    "👨‍✈️ ड्राइवर पैनल" if is_hi else "👨‍✈️ Driver Panel"
])

# ==========================================
# TAB 1: PASSENGER SEARCH & BOOKING
# ==========================================
with t1:
    filter_opts = ["सभी", "टैक्सी / शेयरिंग", "बाइक / स्कूटी"] if is_hi else ["All", "Cab / Shared", "Bike / Scooty"]
    v_filter_disp = st.radio("क्या चाहिए?" if is_hi else "Vehicle Type:", filter_opts, horizontal=True)
    v_map = {
        "सभी": "All", "टैक्सी / शेयरिंग": "Cab / Shared", "बाइक / स्कूटी": "Bike / Scooty",
        "All": "All", "Cab / Shared": "Cab / Shared", "Bike / Scooty": "Bike / Scooty"
    }
    v_filter = v_map[v_filter_disp]

    c1, c2 = st.columns(2)
    with c1:
        p_query = st.text_input(
            "कहाँ से बैठना है? (गाँव / बाज़ार)" if is_hi else "Pickup Village/Market",
            placeholder="जैसे: Someshwar, Bhimtal..."
        )
        p_selected = None
        if len(p_query.strip()) >= 3:
            p_res = search_uk_village(p_query)
            if p_res:
                p_opts = {r["label"]: r for r in p_res}
                p_choice = st.selectbox("पिकअप चुनें:" if is_hi else "Select Pickup:", list(p_opts.keys()), key="p_sel")
                p_selected = p_opts[p_choice]
            else:
                p_selected = {"label": p_query.strip(), "name": p_query.strip(), "lat": None, "lon": None}

    with c2:
        d_query = st.text_input(
            "कहाँ जाना है? (जगह लिखें)" if is_hi else "Drop Village/Market",
            placeholder="जैसे: Almora, Haldwani..."
        )
        d_selected = None
        if len(d_query.strip()) >= 3:
            d_res = search_uk_village(d_query)
            if d_res:
                d_opts = {r["label"]: r for r in d_res}
                d_choice = st.selectbox("ड्रॉप चुनें:" if is_hi else "Select Drop:", list(d_opts.keys()), key="d_sel")
                d_selected = d_opts[d_choice]
            else:
                d_selected = {"label": d_query.strip(), "name": d_query.strip(), "lat": None, "lon": None}

    matched = []
    for trip in active_trips:
        if v_filter != "All" and trip["vehicle_type"] != v_filter:
            continue
        stops_lower = " ".join(trip["stops"]).lower()
        p_name = p_selected["name"] if p_selected else trip["stops"][0]
        d_name = d_selected["name"] if d_selected else trip["stops"][-1]

        if not p_selected and not d_selected:
            matched.append((trip, trip["full_fare"], trip["stops"][0], trip["stops"][-1], None))
        else:
            text_hit = (p_selected and p_selected["name"].lower() in stops_lower) or (d_selected and d_selected["name"].lower() in stops_lower)
            dist_km = round(haversine_km(p_selected["lat"], p_selected["lon"], trip["lat"], trip["lon"]), 1) if (p_selected and p_selected["lat"] and trip.get("lat")) else None
            if text_hit or (dist_km is not None and dist_km <= 20):
                matched.append((trip, trip["full_fare"], p_name, d_name, dist_km))

    if not matched:
        st.warning("इस गाँव के 20 किमी के दायरे में अभी कोई गाड़ी नहीं मिली।" if is_hi else "No rides found within 20 km.")
    else:
        for trip, fare, p_stop, d_stop, dist_km in matched:
            avail_seats = [s for s, status in trip["seats"].items() if status == "Available"]
            avail_count = len(avail_seats)
            fee = max(5, int(round((fare * 0.10) / 5) * 5))

            with st.container(border=True):
                if dist_km is not None and dist_km <= 20:
                    st.caption(f"📍 आपकी लोकेशन से लगभग **{dist_km} किमी** दूर" if is_hi else f"📍 Approx. **{dist_km} km** away")

                if trip["vehicle_type"] == "Bike / Scooty":
                    st.info("🏍️ बाइक / स्कूटी — 1 सवारी, हल्का बैग और हेलमेट ज़रूरी" if is_hi else "🏍️ Bike / Scooty — 1 Rider & Helmet Mandatory")
                elif avail_count == 1:
                    st.error("🔥 सिर्फ़ 1 सीट बची है — तुरंत निकलेगी!" if is_hi else "🔥 Only 1 Seat Left!")
                elif avail_count == 2:
                    st.warning("⚡ सिर्फ़ 2 सीटें बची हैं!" if is_hi else "⚡ Only 2 Seats Left!")
                elif avail_count == 0:
                    st.info("❌ गाड़ी फुल हो चुकी है" if is_hi else "❌ Vehicle Full")
                else:
                    st.success(f"✅ {avail_count} सीटें खाली हैं" if is_hi else f"✅ {avail_count} Seats Available")

                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**{trip['vehicle']}** ✅")
                    st.write(f"🛣️ **रूट:** {' ➔ '.join(trip['stops'])}" if is_hi else f"🛣️ **Route:** {' ➔ '.join(trip['stops'])}")
                    lock_txt = "🔒 *बुकिंग के बाद नंबर दिखेगा*" if is_hi else "🔒 *Unlocks after booking*"
                    st.caption(f"🕒 {trip['time']} | 👤 {trip['driver']} | 📞 {lock_txt}")
                with col_b:
                    st.markdown(f"### ₹{fare}")
                    st.caption(f"+ ₹{fee} शुल्क" if is_hi else f"+ ₹{fee} fee")

                if avail_count > 0:
                    with st.expander("💺 सीट चुनें और बुक करें" if is_hi else "💺 Select Seat & Book"):
                        if trip["vehicle_type"] == "Cab / Shared":
                            st.write("🟩 खाली   |   🟥 बुक है" if is_hi else "🟩 Available   |   🟥 Booked")
                            r1c1, r1c2 = st.columns(2)
                            r1c1.button("🛞 ड्राइवर" if is_hi else "🛞 Driver", disabled=True, key=f"d_{trip['id']}")
                            f1 = trip["seats"].get("Front-1", "Booked")
                            r1c2.button(f"{'🟩' if f1=='Available' else '🟥'} Front-1", disabled=True, key=f"f1_{trip['id']}")
                            m_cols = st.columns(3)
                            for i, s in enumerate(["Mid-1", "Mid-2", "Mid-3"]):
                                sv = trip["seats"].get(s, "Booked")
                                m_cols[i].button(f"{'🟩' if sv=='Available' else '🟥'} {s}", disabled=True, key=f"m_{trip['id']}_{s}")
                            b_cols = st.columns(3)
                            for i, s in enumerate(["Back-1", "Back-2", "Back-3"]):
                                sv = trip["seats"].get(s, "Booked")
                                b_cols[i].button(f"{'🟩' if sv=='Available' else '🟥'} {s}", disabled=True, key=f"b_{trip['id']}_{s}")

                        chosen_seat = st.selectbox("सीट चुनें:" if is_hi else "Choose Seat:", avail_seats, key=f"sel_{trip['id']}")
                        p_user = st.text_input("आपका नाम" if is_hi else "Your Name", key=f"nm_{trip['id']}")
                        p_phone = st.text_input("आपका मोबाइल नंबर" if is_hi else "Mobile Number", key=f"ph_{trip['id']}")

                        btn_lbl = f"✅ बुक करें (किराया ₹{fare} + शुल्क ₹{fee})" if is_hi else f"✅ Confirm (Fare ₹{fare} + Fee ₹{fee})"
                        if st.button(btn_lbl, key=f"bk_{trip['id']}"):
                            if not p_user or not p_phone:
                                st.error("कृपया अपना नाम और मोबाइल नंबर भरें।" if is_hi else "Please enter name and mobile number.")
                            else:
                                trip["seats"][chosen_seat] = "Booked"
                                msg = quote(f"Namaste {trip['driver']} ji, DevBhoomi Ride par {chosen_seat} book ki hai ({p_stop} se {d_stop}). Naam: {p_user}, Phone: {p_phone}")
                                st.session_state.bookings.append({
                                    "bid": len(st.session_state.bookings) + 1, "trip_id": trip["id"],
                                    "passenger": p_user, "seat": chosen_seat, "vehicle": trip["vehicle"],
                                    "route": f"{p_stop} ➔ {d_stop}", "fare": fare, "fee": fee,
                                    "driver": trip["driver"], "phone": trip["phone"],
                                    "wa": f"https://wa.me/91{trip['phone']}?text={msg}", "status": "Confirmed"
                                })
                                st.success("🎉 बुकिंग कन्फर्म! ड्राइवर का नंबर नीचे दिख रहा है।" if is_hi else "🎉 Confirmed! Driver details below.")
                                st.rerun()

    if st.session_state.bookings:
        st.subheader("🔓 आपकी बुकिंग्स (ड्राइवर की जानकारी)" if is_hi else "🔓 Your Bookings")
        for b in reversed(st.session_state.bookings):
            with st.container(border=True):
                if b["status"] == "Cancelled":
                    st.error(f"❌ रद्द की गई — {b['vehicle']} | सीट: {b['seat']}" if is_hi else f"❌ Cancelled — {b['vehicle']}")
                else:
                    st.write(f"**{b['vehicle']}** | सीट: **{b['seat']}** | {b['route']}")
                    st.write(f"ड्राइवर को देना है: **₹{b['fare']}** | बुकिंग शुल्क: ₹{b['fee']}")
                    st.markdown(f"👤 **{b['driver']}** | 📞 **{b['phone']}** | [💬 व्हाट्सएप]({b['wa']})")
                    if st.button("❌ सीट रद्द करें" if is_hi else "❌ Cancel Seat", key=f"cnl_{b['bid']}"):
                        b["status"] = "Cancelled"
                        for t in st.session_state.trips:
                            if t["id"] == b["trip_id"]:
                                t["seats"][b["seat"]] = "Available"
                        st.rerun()

# ==========================================
# TAB 2: LIVE TRACKING
# ==========================================
with t2:
    st.subheader("📍 गाड़ी अभी कहाँ पहुँची है?" if is_hi else "📍 Live Tracking")
    if not active_trips:
        st.info("अभी कोई सक्रिय ट्रिप नहीं है।" if is_hi else "No active trips.")
    else:
        t_map = {f"{t['vehicle']} ({t['stops'][0]} ➔ {t['stops'][-1]})": t for t in active_trips}
        tr = t_map[st.selectbox("गाड़ी चुनें:" if is_hi else "Select Vehicle:", list(t_map.keys()))]
        u_stop = st.selectbox("आप किस स्टॉप पर हैं?" if is_hi else "Your Stop:", tr["stops"], index=min(1, len(tr["stops"]) - 1))

        c_idx, u_idx, delay = tr["current_stop_idx"], tr["stops"].index(u_stop), tr["delay_mins"]
        if delay > 0:
            st.warning(f"⚠️ गाड़ी **{delay} मिनट लेट** है — *{tr['delay_reason']}*")
        else:
            st.success("✅ गाड़ी समय पर चल रही है!" if is_hi else "✅ On Time!")

        for idx, s in enumerate(tr["stops"]):
            if idx < c_idx:
                st.markdown(f"✅ ~~{s}~~")
            elif idx == c_idx:
                st.markdown(f"🚕 **{s} ⬅️ गाड़ी अभी यहाँ है**" if is_hi else f"🚕 **{s} ⬅️ HERE**")
            elif idx == u_idx:
                st.markdown(f"📍 **{s} (आपका स्टॉप)**" if is_hi else f"📍 **{s} (Your Stop)**")
            else:
                st.markdown(f"⚪ {s}")

# ==========================================
# TAB 3: DRIVER PANEL (LOGIN + ₹99 REGISTRATION)
# ==========================================
with t3:
    if st.session_state.logged_in_driver is None:
        st.info("🔒 ड्राइवर पैनल खोलने के लिए लॉगिन करें या नया रजिस्ट्रेशन करें (₹99 एक बार, फिर रोज़ की ट्रिप फ्री)।" if is_hi else "🔒 Login or Register (₹99 one-time fee, then daily trips are free).")
        auth_tab1, auth_tab2 = st.tabs([
            "🔑 ड्राइवर लॉगिन" if is_hi else "🔑 Driver Login",
            "📝 नया रजिस्ट्रेशन (₹99)" if is_hi else "📝 New Registration (₹99)"
        ])

        with auth_tab1:
            login_phone = st.text_input("अपना रजिस्टर्ड मोबाइल नंबर डालें" if is_hi else "Enter Registered Mobile Number", placeholder="जैसे: 9876543210")
            if st.button("🔓 लॉगिन करें" if is_hi else "🔓 Login"):
                if login_phone.strip() in st.session_state.drivers:
                    st.session_state.logged_in_driver = st.session_state.drivers[login_phone.strip()]
                    st.success("✅ लॉगिन सफल!" if is_hi else "✅ Login Successful!")
                    st.rerun()
                else:
                    st.error("❌ यह नंबर रजिस्टर नहीं है। कृपया पहले 'नया रजिस्ट्रेशन' करें।" if is_hi else "❌ Number not registered. Please register first.")

        with auth_tab2:
            st.subheader("नया ड्राइवर रजिस्ट्रेशन (एक बार ₹99 शुल्क)" if is_hi else "New Driver Registration (₹99 One-Time)")
            with st.form("driver_reg_form"):
                r_name = st.text_input("ड्राइवर का पूरा नाम" if is_hi else "Full Name", placeholder="मनोज जोशी")
                r_phone = st.text_input("मोबाइल नंबर (यही आपकी ID होगी)" if is_hi else "Mobile Number (Your Login ID)", placeholder="10 अंकों का नंबर")
                r_addr = st.text_area("पूरा पता (गाँव / शहर / जिला)" if is_hi else "Full Address", placeholder="गाँव, पोस्ट, जिला...")
                vt_opts = ["टैक्सी / शेयरिंग", "बाइक / स्कूटी"] if is_hi else ["Cab / Shared", "Bike / Scooty"]
                r_vtype_disp = st.radio("गाड़ी का प्रकार:" if is_hi else "Vehicle Type:", vt_opts, horizontal=True)
                r_vtype = "Bike / Scooty" if r_vtype_disp in ["बाइक / स्कूटी", "Bike / Scooty"] else "Cab / Shared"
                r_veh = st.text_input("गाड़ी का नाम और नंबर" if is_hi else "Vehicle Name & Number", placeholder="Bolero UK 04 TA 9988")
                r_dl = st.text_input("ड्राइविंग लाइसेंस नंबर (DL No.)" if is_hi else "Driving License Number", placeholder="UK0420200012345")

                st.warning("💳 **रजिस्ट्रेशन शुल्क: ₹99 (केवल एक बार)** — इसके बाद रोज़ की ट्रिप डालना लाइफटाइम फ्री रहेगा।" if is_hi else "💳 **Registration Fee: ₹99 (One-Time)** — Daily trip posting is free for life.")
                paid_confirm = st.checkbox("✅ मैंने ₹99 रजिस्ट्रेशन शुल्क जमा कर दिया है (Demo)" if is_hi else "✅ I have paid ₹99 Registration Fee (Demo)")

                if st.form_submit_button("🚀 रजिस्ट्रेशन पूरा करें और पैनल खोलें" if is_hi else "🚀 Complete Registration"):
                    if not (r_name and r_phone and r_addr and r_veh and r_dl):
                        st.error("कृपया सभी जानकारी भरें।" if is_hi else "Please fill all fields.")
                    elif r_phone.strip() in st.session_state.drivers:
                        st.warning("यह मोबाइल नंबर पहले से रजिस्टर्ड है! कृपया लॉगिन करें।" if is_hi else "Already registered! Please login.")
                    elif not paid_confirm:
                        st.error("रजिस्ट्रेशन के लिए ₹99 शुल्क कन्फर्म करना ज़रूरी है।" if is_hi else "Please confirm ₹99 fee.")
                    else:
                        new_drv = {
                            "name": r_name.strip(), "phone": r_phone.strip(), "address": r_addr.strip(),
                            "vehicle_type": r_vtype, "vehicle": r_veh.strip(), "license": r_dl.strip(), "reg_paid": True
                        }
                        st.session_state.drivers[r_phone.strip()] = new_drv
                        st.session_state.logged_in_driver = new_drv
                        st.success("🎉 बधाई हो! आपका रजिस्ट्रेशन हो गया है। अब आप रोज़ फ्री में ट्रिप डाल सकते हैं।" if is_hi else "🎉 Registration Complete!")
                        st.rerun()
    else:
        drv = st.session_state.logged_in_driver
        c_top1, c_top2 = st.columns([3, 1])
        c_top1.success(f"👤 स्वागत है, **{drv['name']}** ({drv['vehicle']}) ✅" if is_hi else f"👤 Welcome, **{drv['name']}** ✅")
        if c_top2.button("🚪 लॉगआउट" if is_hi else "🚪 Logout"):
            st.session_state.logged_in_driver = None
            st.rerun()

        d1, d2 = st.tabs([
            "➕ आज की ट्रिप डालें (फ्री)" if is_hi else "➕ Add Today's Trip (Free)",
            "📡 लोकेशन अपडेट / ट्रिप रद्द करें" if is_hi else "📡 Update Location / Cancel"
        ])

        with d1:
            start_search = st.text_input(
                "आपकी गाड़ी अभी किस गाँव / बाज़ार में है? (खोजें)" if is_hi else "Current Village/Market (Search)",
                placeholder="जैसे: Kausani, Someshwar, Gairsain..."
            )
            drv_lat, drv_lon, drv_start_name = None, None, start_search.strip()
            if len(start_search.strip()) >= 3:
                s_res = search_uk_village(start_search)
                if s_res:
                    s_opts = {r["label"]: r for r in s_res}
                    s_pick = st.selectbox("अपना सही गाँव चुनें:" if is_hi else "Select exact village:", list(s_opts.keys()), key="drv_loc")
                    drv_lat, drv_lon, drv_start_name = s_opts[s_pick]["lat"], s_opts[s_pick]["lon"], s_opts[s_pick]["name"]

            with st.form("add_trip"):
                d_stops = st.text_input("आगे के स्टॉप (कॉमा लगाकर लिखें)" if is_hi else "Route Stops (comma separated)", placeholder="जैसे: Someshwar, Kosi, Almora")
                c1, c2 = st.columns(2)
                d_time = c1.text_input("निकलने का समय" if is_hi else "Departure Time", placeholder="09:00 AM")
                d_fare = c2.number_input("आज का किराया (₹)" if is_hi else "Today's Fare (₹)", min_value=20, value=150, step=10)
                booked_cnt = st.slider("टैक्सी के लिए: कितनी सीटें पहले से बुक हैं?" if is_hi else "Seats already booked", 0, 6, 3)

                if st.form_submit_button("🚀 गाड़ी ऑनलाइन डालें" if is_hi else "🚀 Publish Trip"):
                    if d_stops or drv_start_name:
                        s_list = [x.strip() for x in d_stops.split(",") if x.strip()]
                        if drv_start_name and (not s_list or drv_start_name.lower() != s_list[0].lower()):
                            s_list.insert(0, drv_start_name)
                        if drv["vehicle_type"] == "Bike / Scooty":
                            s_map = {"Pillion-Seat": "Available"}
                        else:
                            names = ["Front-1", "Mid-1", "Mid-2", "Mid-3", "Back-1", "Back-2", "Back-3"]
                            s_map = {s: ("Booked" if i < booked_cnt else "Available") for i, s in enumerate(names)}
                        st.session_state.trips.append({
                            "id": len(st.session_state.trips) + 1, "driver": drv["name"], "phone": drv["phone"],
                            "vehicle_type": drv["vehicle_type"], "vehicle": drv["vehicle"], "stops": s_list,
                            "lat": drv_lat, "lon": drv_lon, "time": d_time, "full_fare": d_fare,
                            "current_stop_idx": 0, "delay_mins": 0, "delay_reason": "समय पर",
                            "status": "Active", "seats": s_map
                        })
                        st.success("✅ आपकी गाड़ी लाइव हो गई है!" if is_hi else "✅ Trip is now live!")
                        st.rerun()
                    else:
                        st.error("कृपया अपना गाँव या रूट ज़रूर लिखें।" if is_hi else "Please enter route stops.")

        with d2:
            my_trips = [t for t in active_trips if t["phone"] == drv["phone"]]
            if not my_trips:
                st.info("आपकी अभी कोई सक्रिय ट्रिप नहीं है।" if is_hi else "You have no active trips.")
            else:
                d_map = {f"{t['vehicle']} ({t['stops'][0]} ➔ {t['stops'][-1]})": t for t in my_trips}
                st_trip = d_map[st.selectbox("अपनी ट्रिप चुनें:" if is_hi else "Select Your Trip:", list(d_map.keys()))]
                n_stop = st.selectbox("अभी कहाँ पहुँचे हैं?" if is_hi else "Current Location:", st_trip["stops"], index=st_trip["current_stop_idx"])
                n_delay = st.radio("क्या गाड़ी लेट है?" if is_hi else "Delay:", [0, 10, 20, 30], format_func=lambda x: ("समय पर" if is_hi else "On Time") if x == 0 else f"+{x} min", horizontal=True)
                n_reason = st.text_input("लेट होने का कारण" if is_hi else "Delay Reason", value=st_trip["delay_reason"])

                col_u, col_c = st.columns(2)
                if col_u.button("📡 लोकेशन अपडेट करें" if is_hi else "📡 Update Location"):
                    st_trip["current_stop_idx"] = st_trip["stops"].index(n_stop)
                    st_trip["delay_mins"] = n_delay
                    st_trip["delay_reason"] = ("समय पर" if is_hi else "On Time") if n_delay == 0 else n_reason
                    st.success("✅ लोकेशन अपडेट हो गई!")
                    st.rerun()
                if col_c.button("🚫 पूरी ट्रिप रद्द करें" if is_hi else "🚫 Cancel Trip"):
                    st_trip["status"] = "Cancelled"
                    st.error("ट्रिप रद्द कर दी गई है।")
                    st.rerun()
