import streamlit as st
import requests
import math
import json
import re
from urllib.parse import quote

st.set_page_config(page_title="DevBhoomi Ride", page_icon="🏔️", layout="centered")

DB_URL = "https://script.google.com/macros/s/AKfycby3A2XJ0_hrgcs0IRy-pnJzQWmXmwrndsQXZEN73EjNoKKlSIW83dxnjqGp4L6yZ15heQ/exec"
SUPPORT_WHATSAPP = "919456136422"  # <-- Yahan 91 ke saath apna Support WhatsApp number daalein

# --- GOOGLE SHEETS DATABASE FUNCTIONS ---
@st.cache_data(ttl=15)
def load_db():
    try:
        res = requests.get(DB_URL, timeout=10)
        if res.status_code == 200:
            raw = res.json()
            drivers = {}
            for d in raw.get("drivers", []):
                ph = str(d.get("phone", "")).strip()
                if ph:
                    raw_lic = str(d.get("license", ""))
                    if " | PIN:" in raw_lic:
                        lic_part, pin_part = raw_lic.split(" | PIN:", 1)
                        pin_val = pin_part.strip()
                    else:
                        lic_part, pin_val = raw_lic, "1234"
                    drivers[ph] = {
                        "phone": ph, "name": str(d.get("name", "")),
                        "address": str(d.get("address", "")),
                        "vehicle_type": str(d.get("vehicle_type", "Cab / Shared")),
                        "vehicle": str(d.get("vehicle", "")),
                        "license": lic_part.strip(), "pin": pin_val, "reg_paid": True
                    }
            trips = []
            for t in raw.get("trips", []):
                if not t.get("id"):
                    continue
                stops = t.get("stops", "[]")
                seats = t.get("seats", "{}")
                stops = json.loads(stops) if isinstance(stops, str) else stops
                seats = json.loads(seats) if isinstance(seats, str) else seats
                lat = float(t["lat"]) if str(t.get("lat", "")).strip() != "" else None
                lon = float(t["lon"]) if str(t.get("lon", "")).strip() != "" else None
                trips.append({
                    "id": int(t["id"]), "driver": str(t.get("driver", "")),
                    "phone": str(t.get("phone", "")).strip(),
                    "vehicle_type": str(t.get("vehicle_type", "Cab / Shared")),
                    "vehicle": str(t.get("vehicle", "")), "stops": stops,
                    "lat": lat, "lon": lon, "time": str(t.get("time", "")),
                    "full_fare": int(float(t.get("full_fare", 0))),
                    "current_stop_idx": int(float(t.get("current_stop_idx", 0))),
                    "delay_mins": int(float(t.get("delay_mins", 0))),
                    "delay_reason": str(t.get("delay_reason", "समय पर")),
                    "status": str(t.get("status", "Active")), "seats": seats
                })
            bookings = []
            for b in raw.get("bookings", []):
                if not b.get("bid"):
                    continue
                ph = str(b.get("phone", "")).strip()
                msg = quote(
                    f"नमस्ते {b.get('driver','')} जी, मैंने DevBhoomi Ride पर बुकिंग की है:\n"
                    f"विवरण: {b.get('seat','')}\nरूट: {b.get('route','')}\n"
                    f"किराया: ₹{b.get('fare','')}\nसवारी: {b.get('passenger','')}"
                )
                bookings.append({
                    "bid": int(b["bid"]), "trip_id": int(b["trip_id"]),
                    "passenger": str(b.get("passenger", "")), "seat": str(b.get("seat", "")),
                    "vehicle": str(b.get("vehicle", "")), "route": str(b.get("route", "")),
                    "fare": int(float(b.get("fare", 0))), "fee": int(float(b.get("fee", 0))),
                    "driver": str(b.get("driver", "")), "phone": ph,
                    "wa": f"https://wa.me/91{ph}?text={msg}",
                    "status": str(b.get("status", "Confirmed"))
                })
            return drivers, trips, bookings
    except Exception:
        pass
    return {}, [], []

def post_db(payload):
    try:
        requests.post(DB_URL, json=payload, timeout=10)
        load_db.clear()
        return True
    except Exception:
        return False

# --- FREE UTTARAKHAND VILLAGE SEARCH ---
@st.cache_data(ttl=3600)
def search_uk_village(query):
    if not query or len(query.strip()) < 3:
        return []
    try:
        url = "https://photon.komoot.io/api/"
        params = {"q": f"{query.strip()} Uttarakhand India", "limit": 6}
        res = requests.get(url, params=params, headers={"User-Agent": "DevBhoomiRide/1.0"}, timeout=5)
        if res.status_code == 200:
            results, seen = [], set()
            for f in res.json().get("features", []):
                props = f.get("properties", {})
                coords = f.get("geometry", {}).get("coordinates", [None, None])
                name = props.get("name", "")
                dist = props.get("county") or props.get("city") or props.get("state_district") or ""
                state = props.get("state", "")
                if name and ("Uttarakhand" in state or "India" in props.get("country", "")):
                    label = f"{name}, {dist}" if dist and dist != name else name
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
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# --- LOAD LIVE DATA ---
drivers_db, trips_db, all_bookings_db = load_db()
bookings_db = [b for b in all_bookings_db if b["trip_id"] != 0]
active_local_trips = [t for t in trips_db if t["status"] == "Active" and t["vehicle_type"] != "CharDham"]
active_cd_trips = [t for t in trips_db if t["status"] == "Active" and t["vehicle_type"] == "CharDham"]
trips_by_id = {t["id"]: t for t in trips_db}

if "logged_in_driver" not in st.session_state:
    st.session_state.logged_in_driver = None
if "last_p_phone" not in st.session_state:
    st.session_state.last_p_phone = ""
if "latest_wa_alert" not in st.session_state:
    st.session_state.latest_wa_alert = None
if "cancel_wa_alert" not in st.session_state:
    st.session_state.cancel_wa_alert = None

# --- LANGUAGE SWITCH & HEADER ---
c_lang, c_ref = st.columns([3, 1])
lang = c_lang.radio("🌐 भाषा चुनें / Language:", ["हिंदी", "English"], horizontal=True)
is_hi = (lang == "हिंदी")
if c_ref.button("🔄 रिफ्रेश" if is_hi else "🔄 Refresh"):
    load_db.clear()
    st.rerun()

st.title("🏔️ देवभूमि राइड" if is_hi else "🏔️ DevBhoomi Ride")
st.caption("उत्तराखंड के हर गाँव से बाज़ार और चारधाम यात्रा तक — टैक्सी, बाइक और स्कूटी" if is_hi else "Uttarakhand Villages to City & Char Dham Yatra — Cab, Bike & Scooty")

t1, t_cd, t_my, t2, t3 = st.tabs([
    "🔍 सीट बुक" if is_hi else "🔍 Book Ride",
    "🕉️ चारधाम यात्रा" if is_hi else "🕉️ Char Dham",
    "🎫 मेरी बुकिंग" if is_hi else "🎫 My Bookings",
    "📍 लाइव" if is_hi else "📍 Live Track",
    "👨‍✈️ ड्राइवर पैनल" if is_hi else "👨‍✈️ Driver Panel"
])

# ==========================================
# TAB 1: PASSENGER LOCAL SEARCH & BOOKING
# ==========================================
with t1:
    if st.session_state.latest_wa_alert:
        wa_info = st.session_state.latest_wa_alert
        with st.container(border=True):
            st.success(
                f"🎉 बुकिंग कन्फर्म हो गई! ({wa_info['seat']}) | ड्राइवर: **{wa_info['driver']}** (📞 {wa_info['phone']})"
                if is_hi else
                f"🎉 Booking Confirmed! ({wa_info['seat']}) | Driver: **{wa_info['driver']}** (📞 {wa_info['phone']})"
            )
            st.link_button(
                "📲 ड्राइवर को व्हाट्सएप पर बुकिंग भेजें (तुरंत सूचित करें)" if is_hi else "📲 Send Booking Alert to Driver on WhatsApp",
                wa_info["wa_url"],
                type="primary",
                use_container_width=True
            )
            if st.button("✖️ बंद करें" if is_hi else "✖️ Dismiss", key="dismiss_wa"):
                st.session_state.latest_wa_alert = None
                st.rerun()

    f_opts = ["सभी", "टैक्सी / शेयरिंग", "बाइक / स्कूटी"] if is_hi else ["All", "Cab / Shared", "Bike / Scooty"]
    v_disp = st.radio("क्या चाहिए?" if is_hi else "Vehicle Type:", f_opts, horizontal=True)
    v_map = {
        "सभी": "All", "टैक्सी / शेयरिंग": "Cab / Shared", "बाइक / स्कूटी": "Bike / Scooty",
        "All": "All", "Cab / Shared": "Cab / Shared", "Bike / Scooty": "Bike / Scooty"
    }
    v_filter = v_map[v_disp]

    c1, c2 = st.columns(2)
    with c1:
        p_q = st.text_input("कहाँ से बैठना है? (गाँव / बाज़ार)" if is_hi else "Pickup Village/Market", placeholder="जैसे: Someshwar, Bhimtal...")
        p_sel = None
        if len(p_q.strip()) >= 3:
            p_res = search_uk_village(p_q)
            if p_res:
                p_opts = {r["label"]: r for r in p_res}
                p_sel = p_opts[st.selectbox("पिकअप चुनें:" if is_hi else "Select Pickup:", list(p_opts.keys()), key="p_sel")]
            else:
                p_sel = {"label": p_q.strip(), "name": p_q.strip(), "lat": None, "lon": None}

    with c2:
        d_q = st.text_input("कहाँ जाना है? (जगह लिखें)" if is_hi else "Drop Village/Market", placeholder="जैसे: Almora, Haldwani...")
        d_sel = None
        if len(d_q.strip()) >= 3:
            d_res = search_uk_village(d_q)
            if d_res:
                d_opts = {r["label"]: r for r in d_res}
                d_sel = d_opts[st.selectbox("ड्रॉप चुनें:" if is_hi else "Select Drop:", list(d_opts.keys()), key="d_sel")]
            else:
                d_sel = {"label": d_q.strip(), "name": d_q.strip(), "lat": None, "lon": None}

    matched = []
    for trip in active_local_trips:
        if v_filter != "All" and trip["vehicle_type"] != v_filter:
            continue
        stops_l = " ".join(trip["stops"]).lower()
        p_name = p_sel["name"] if p_sel else (trip["stops"][0] if trip["stops"] else "")
        d_name = d_sel["name"] if d_sel else (trip["stops"][-1] if trip["stops"] else "")

        if not p_sel and not d_sel:
            matched.append((trip, trip["full_fare"], p_name, d_name, None))
        else:
            hit = (p_sel and p_sel["name"].lower() in stops_l) or (d_sel and d_sel["name"].lower() in stops_l)
            dist_km = round(haversine_km(p_sel["lat"], p_sel["lon"], trip["lat"], trip["lon"]), 1) if (p_sel and p_sel["lat"] and trip.get("lat")) else None
            if hit or (dist_km is not None and dist_km <= 20):
                matched.append((trip, trip["full_fare"], p_name, d_name, dist_km))

    if not matched:
        st.warning("अभी कोई लाइव गाड़ी नहीं मिली। ड्राइवर पैनल से नई ट्रिप डालें!" if is_hi else "No active rides found.")
    else:
        for trip, fare, p_stop, d_stop, dist_km in matched:
            avail_seats = [s for s, status in trip["seats"].items() if status == "Available"]
            avail_cnt = len(avail_seats)
            fee = max(5, int(round((fare * 0.10) / 5) * 5))

            with st.container(border=True):
                if dist_km is not None and dist_km <= 20:
                    st.caption(f"📍 आपकी लोकेशन से लगभग **{dist_km} किमी** दूर" if is_hi else f"📍 Approx. **{dist_km} km** away")

                if trip["vehicle_type"] == "Bike / Scooty":
                    st.info("🏍️ बाइक / स्कूटी — 1 सवारी, हल्का बैग और हेलमेट ज़रूरी" if is_hi else "🏍️ Bike / Scooty — 1 Rider & Helmet Mandatory")
                elif avail_cnt == 1:
                    st.error("🔥 सिर्फ़ 1 सीट बची है — तुरंत निकलेगी!" if is_hi else "🔥 Only 1 Seat Left!")
                elif avail_cnt == 2:
                    st.warning("⚡ सिर्फ़ 2 सीटें बची हैं!" if is_hi else "⚡ Only 2 Seats Left!")
                elif avail_cnt == 0:
                    st.info("❌ गाड़ी फुल हो चुकी है" if is_hi else "❌ Vehicle Full")
                else:
                    st.success(f"✅ {avail_cnt} सीटें खाली हैं" if is_hi else f"✅ {avail_cnt} Seats Available")

                ca, cb = st.columns([3, 1])
                with ca:
                    st.markdown(f"**{trip['vehicle']}** ✅")
                    st.write(f"🛣️ **रूट:** {' ➔ '.join(trip['stops'])}" if is_hi else f"🛣️ **Route:** {' ➔ '.join(trip['stops'])}")
                    lock_txt = "🔒 *बुकिंग के बाद नंबर दिखेगा*" if is_hi else "🔒 *Unlocks after booking*"
                    st.caption(f"🕒 {trip['time']} | 👤 {trip['driver']} | 📞 {lock_txt}")
                with cb:
                    st.markdown(f"### ₹{fare}")
                    st.caption(f"+ ₹{fee} शुल्क" if is_hi else f"+ ₹{fee} fee")

                if avail_cnt > 0:
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

                        chosen = st.selectbox("सीट चुनें:" if is_hi else "Choose Seat:", avail_seats, key=f"sel_{trip['id']}")
                        p_user = st.text_input("आपका नाम" if is_hi else "Your Name", key=f"nm_{trip['id']}")
                        p_phone = st.text_input("आपका 10 अंकों का मोबाइल नंबर" if is_hi else "10-digit Mobile Number", key=f"ph_{trip['id']}")

                        btn_lbl = f"✅ बुक करें (किराया ₹{fare} + शुल्क ₹{fee})" if is_hi else f"✅ Confirm (Fare ₹{fare} + Fee ₹{fee})"
                        if st.button(btn_lbl, key=f"bk_{trip['id']}"):
                            if not p_user.strip() or len(p_phone.strip()) < 10:
                                st.error("कृपया सही नाम और 10 अंकों का मोबाइल नंबर भरें।" if is_hi else "Please enter name and 10-digit mobile number.")
                            else:
                                new_seats = dict(trip["seats"])
                                new_seats[chosen] = "Booked"
                                new_bid = (max([b["bid"] for b in all_bookings_db]) + 1) if all_bookings_db else 1
                                b_data = {
                                    "bid": new_bid, "trip_id": trip["id"],
                                    "passenger": f"{p_user.strip()} ({p_phone.strip()})",
                                    "seat": chosen, "vehicle": trip["vehicle"],
                                    "route": f"{p_stop} ➔ {d_stop}",
                                    "fare": fare, "fee": fee, "driver": trip["driver"], "phone": trip["phone"]
                                }
                                with st.spinner("बुकिंग सेव हो रही है..." if is_hi else "Saving booking..."):
                                    post_db({"action": "update_trip", "id": trip["id"], "seats": new_seats})
                                    post_db({"action": "add_booking", "booking": b_data})
                                wa_msg = quote(
                                    f"नमस्ते {trip['driver']} जी, मैंने DevBhoomi Ride पर नई सीट बुक की है:\n"
                                    f"सीट: {chosen}\nरूट: {p_stop} से {d_stop}\nसमय: {trip['time']}\n"
                                    f"किराया: ₹{fare}\nसवारी: {p_user.strip()} ({p_phone.strip()})"
                                )
                                st.session_state.last_p_phone = p_phone.strip()
                                st.session_state.latest_wa_alert = {
                                    "seat": chosen, "driver": trip["driver"], "phone": trip["phone"],
                                    "wa_url": f"https://wa.me/91{trip['phone']}?text={wa_msg}"
                                }
                                st.rerun()

# ==========================================
# TAB 2: CHAR DHAM YATRA (DIRECT APP BOOKING)
# ==========================================
with t_cd:
    st.subheader("🕉️ चारधाम यात्रा — वेरिफाइड पहाड़ी ड्राइवर बुक करें" if is_hi else "🕉️ Char Dham Yatra — Book Verified Local Cabs")
    if st.session_state.latest_wa_alert:
        wa_info = st.session_state.latest_wa_alert
        with st.container(border=True):
            st.success(f"🎉 चारधाम बुकिंग कन्फर्म! ड्राइवर: **{wa_info['driver']}** (📞 {wa_info['phone']})" if is_hi else f"🎉 Char Dham Booking Confirmed! Driver: **{wa_info['driver']}** (📞 {wa_info['phone']})")
            st.link_button("📲 ड्राइवर को व्हाट्सएप पर बुकिंग भेजें" if is_hi else "📲 Send Booking on WhatsApp", wa_info["wa_url"], type="primary", use_container_width=True)

    fc1, fc2 = st.columns(2)
    f_pick = fc1.selectbox("पिकअप शहर:" if is_hi else "Pickup City:", ["सभी / All", "Haridwar", "Rishikesh", "Dehradun", "Delhi / NCR", "Kathgodam / Haldwani"])
    f_dham = fc2.selectbox("धाम चुनें:" if is_hi else "Select Dham:", ["सभी / All", "Poora Char Dham", "Do Dham", "Kedarnath", "Badrinath", "Gangotri / Yamunotri"])

    cd_matched = []
    for trip in active_cd_trips:
        r_str = " ".join(trip["stops"]).lower()
        ok_p = (f_pick == "सभी / All") or (f_pick.split(" /")[0].lower() in r_str)
        ok_d = (f_dham == "सभी / All") or (f_dham.split(" /")[0].lower() in r_str)
        if ok_p and ok_d:
            cd_matched.append(trip)

    if not cd_matched:
        st.info("अभी इस रूट पर कोई चारधाम गाड़ी ऑनलाइन नहीं है। ड्राइवर पैनल से नई चारधाम ट्रिप डालें!" if is_hi else "No Char Dham cabs listed yet. Drivers can post from Driver Panel!")
    else:
        for trip in cd_matched:
            avail_opts = [s for s, status in trip["seats"].items() if status == "Available"]
            fare = trip["full_fare"]
            with st.container(border=True):
                if not avail_opts:
                    st.info("❌ यह गाड़ी बुक हो चुकी है" if is_hi else "❌ Already Booked")
                else:
                    st.success("🏔️ वेरिफाइड पहाड़ी ड्राइवर — बुकिंग के लिए उपलब्ध" if is_hi else "🏔️ Verified Local Driver — Available")

                ca, cb = st.columns([3, 1])
                with ca:
                    st.markdown(f"**🕉️ {trip['vehicle']}** ✅")
                    st.write(f"🛣️ **यात्रा:** {' ➔ '.join(trip['stops'])}" if is_hi else f"🛣️ **Yatra:** {' ➔ '.join(trip['stops'])}")
                    lock_txt = "🔒 *बुकिंग के बाद नंबर दिखेगा*" if is_hi else "🔒 *Unlocks after booking*"
                    st.caption(f"📅 {trip['time']} | 👤 {trip['driver']} | 📞 {lock_txt}")
                with cb:
                    st.markdown(f"### ₹{fare}")
                    st.caption("पैकेज रेट" if is_hi else "Package")

                if avail_opts:
                    with st.expander("🚕 यह गाड़ी बुक करें (नंबर अनलॉक करें)" if is_hi else "🚕 Book This Cab (Unlock Number)"):
                        cd_chosen = st.selectbox("विकल्प चुनें:" if is_hi else "Select Option:", avail_opts, key=f"cd_sel_{trip['id']}")
                        cd_date_u = st.text_input("आपकी यात्रा की तारीख (Date):" if is_hi else "Your Travel Date:", placeholder="जैसे: 15 May 2026", key=f"cd_dt_{trip['id']}")
                        cd_uname = st.text_input("आपका नाम:" if is_hi else "Your Name:", key=f"cd_nm_{trip['id']}")
                        cd_uphone = st.text_input("आपका 10 अंकों का मोबाइल नंबर:" if is_hi else "10-digit Mobile Number:", key=f"cd_ph_{trip['id']}")

                        if st.button(f"✅ चारधाम बुकिंग कन्फर्म करें (₹{fare})" if is_hi else f"✅ Confirm Char Dham Booking (₹{fare})", key=f"cd_bk_{trip['id']}", type="primary"):
                            if not (cd_uname.strip() and len(cd_uphone.strip()) >= 10 and cd_date_u.strip()):
                                st.error("कृपया नाम, तारीख और 10 अंकों का मोबाइल नंबर भरें।" if is_hi else "Please fill name, date and 10-digit phone.")
                            else:
                                new_seats = dict(trip["seats"])
                                new_seats[cd_chosen] = "Booked"
                                new_bid = (max([b["bid"] for b in all_bookings_db]) + 1) if all_bookings_db else 1
                                route_txt = " ➔ ".join(trip["stops"])
                                b_data = {
                                    "bid": new_bid, "trip_id": trip["id"],
                                    "passenger": f"{cd_uname.strip()} ({cd_uphone.strip()})",
                                    "seat": f"{cd_chosen} | {cd_date_u.strip()}",
                                    "vehicle": trip["vehicle"], "route": route_txt,
                                    "fare": fare, "fee": 0, "driver": trip["driver"], "phone": trip["phone"]
                                }
                                with st.spinner("चारधाम बुकिंग सेव हो रही है..."):
                                    post_db({"action": "update_trip", "id": trip["id"], "seats": new_seats})
                                    post_db({"action": "add_booking", "booking": b_data})
                                wa_msg = quote(
                                    f"नमस्ते {trip['driver']} जी, मैंने DevBhoomi Ride पर आपकी चारधाम गाड़ी बुक की है:\n"
                                    f"यात्रा: {route_txt}\nतारीख: {cd_date_u.strip()}\nविकल्प: {cd_chosen}\n"
                                    f"रेट: ₹{fare}\nयात्री: {cd_uname.strip()} ({cd_uphone.strip()})"
                                )
                                st.session_state.last_p_phone = cd_uphone.strip()
                                st.session_state.latest_wa_alert = {
                                    "seat": f"{cd_chosen} ({cd_date_u.strip()})", "driver": trip["driver"], "phone": trip["phone"],
                                    "wa_url": f"https://wa.me/91{trip['phone']}?text={wa_msg}"
                                }
                                st.rerun()

    st.divider()
    st.caption("• पहाड़ों पर चढ़ाई के समय AC बंद रहता है। • टोल/पार्किंग की बात ड्राइवर से कन्फर्म कर लें। • आपातकालीन सहायता: **112**" if is_hi else "• AC is off on steep climbs. • Confirm toll/parking with driver. • Emergency: **112**")
    st.link_button("🏛️ Official Uttarakhand Char Dham Yatra Registration Portal", "https://registrationandtouristcare.uk.gov.in/", use_container_width=True)

# ==========================================
# TAB 3: MY BOOKINGS (PASSENGER VIEW)
# ==========================================
with t_my:
    if st.session_state.cancel_wa_alert:
        c_info = st.session_state.cancel_wa_alert
        with st.container(border=True):
            st.warning("बुकिंग रद्द हो गई है। ड्राइवर को नीचे दिए बटन से व्हाट्सएप पर सूचित कर दें:" if is_hi else "Booking cancelled. Notify driver on WhatsApp:")
            st.link_button(
                "📲 ड्राइवर को कैंसिल की सूचना व्हाट्सएप पर भेजें" if is_hi else "📲 Send Cancellation Alert on WhatsApp",
                c_info["wa_url"],
                type="primary",
                use_container_width=True
            )
            if st.button("✖️ बंद करें" if is_hi else "✖️ Dismiss", key="dismiss_cwa"):
                st.session_state.cancel_wa_alert = None
                st.rerun()

    st.subheader("🎫 अपनी बुक की हुई टिकट देखें" if is_hi else "🎫 Check Your Booked Tickets")
    chk_phone = st.text_input(
        "बुकिंग के समय डाला गया मोबाइल नंबर लिखें:" if is_hi else "Enter Mobile Number used for booking:",
        value=st.session_state.last_p_phone,
        placeholder="जैसे: 9876543210"
    ).strip()

    if len(chk_phone) >= 10:
        my_list = [b for b in bookings_db if chk_phone in b["passenger"]]
        if not my_list:
            st.info("इस नंबर पर कोई बुकिंग नहीं मिली।" if is_hi else "No bookings found for this number.")
        else:
            for b in reversed(my_list):
                t_info = trips_by_id.get(b["trip_id"], {})
                t_time = t_info.get("time", "समय उपलब्ध नहीं")
                t_status = t_info.get("status", "Active")
                with st.container(border=True):
                    if b["status"] == "Cancelled":
                        st.error(f"❌ रद्द की गई — {b['vehicle']} | {b['seat']}" if is_hi else f"❌ Cancelled — {b['vehicle']} | {b['seat']}")
                    else:
                        if t_status == "Cancelled":
                            st.warning("⚠️ ध्यान दें: ड्राइवर ने यह ट्रिप रद्द कर दी है।" if is_hi else "⚠️ Note: Driver cancelled this trip.")
                        else:
                            st.success(f"✅ कन्फर्म — **{b['seat']}** | 🕒 {t_time}" if is_hi else f"✅ Confirmed — **{b['seat']}** | 🕒 {t_time}")
                        st.write(f"🚕 **{b['vehicle']}** | 🛣️ {b['route']}")
                        st.write(f"💰 ड्राइवर को देना है: **₹{b['fare']}** | बुकिंग शुल्क: ₹{b['fee']}" if is_hi else f"💰 Pay Driver: **₹{b['fare']}** | Fee: ₹{b['fee']}")
                        st.write(f"👤 **{b['driver']}** | 📞 **{b['phone']}**")
                        st.link_button(
                            "📲 ड्राइवर को व्हाट्सएप करें" if is_hi else "📲 WhatsApp Driver",
                            b["wa"],
                            type="primary",
                            use_container_width=True
                        )
                        if st.button("❌ बुकिंग रद्द करें" if is_hi else "❌ Cancel Booking", key=f"cnl_{b['bid']}"):
                            with st.spinner("रद्द हो रहा है..."):
                                post_db({"action": "cancel_booking", "bid": b["bid"]})
                                if b["trip_id"] in trips_by_id:
                                    upd_seats = dict(trips_by_id[b["trip_id"]]["seats"])
                                    seat_key = b["seat"].split(" | ")[0]
                                    if seat_key in upd_seats:
                                        upd_seats[seat_key] = "Available"
                                        post_db({"action": "update_trip", "id": b["trip_id"], "seats": upd_seats})
                            c_msg = quote(f"नमस्ते {b['driver']} जी, मैंने DevBhoomi Ride पर अपनी बुकिंग ({b['seat']}, {b['route']}) रद्द कर दी है। — {b['passenger']}")
                            st.session_state.cancel_wa_alert = {"wa_url": f"https://wa.me/91{b['phone']}?text={c_msg}"}
                            st.rerun()
    else:
        st.caption("अपनी पुरानी या कल की बुकिंग देखने के लिए ऊपर 10 अंकों का मोबाइल नंबर डालें।" if is_hi else "Enter your 10-digit mobile number to view your tickets anytime.")

# ==========================================
# TAB 4: LIVE TRACKING
# ==========================================
with t2:
    st.subheader("📍 गाड़ी अभी कहाँ पहुँची है?" if is_hi else "📍 Live Tracking")
    if not active_local_trips:
        st.info("अभी कोई सक्रिय लोकल ट्रिप नहीं है।" if is_hi else "No active local trips.")
    else:
        t_map = {f"{t['vehicle']} ({t['stops'][0]} ➔ {t['stops'][-1]})": t for t in active_local_trips if t["stops"]}
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
# TAB 5: DRIVER PANEL (4-DIGIT PIN + FREE CHAR DHAM TRIP)
# ==========================================
with t3:
    if st.session_state.logged_in_driver is None:
        st.subheader("👨‍✈️ ड्राइवर रजिस्ट्रेशन / लॉगिन" if is_hi else "👨‍✈️ Driver Registration / Login")
        ph_in = st.text_input(
            "अपना 10 अंकों का मोबाइल नंबर डालें:" if is_hi else "Enter your 10-digit Mobile Number:",
            placeholder="जैसे: 9876543210"
        ).strip()

        if len(ph_in) >= 10:
            if ph_in in drivers_db:
                st.success("✅ आपका नंबर पहले से रजिस्टर्ड है! लॉगिन के लिए अपना 4 अंकों का PIN डालें:" if is_hi else "✅ Registered! Enter your 4-digit PIN:")
                with st.form("driver_login_form"):
                    pin_in = st.text_input("🔐 4 अंकों का PIN" if is_hi else "🔐 4-Digit PIN", type="password", max_chars=4)
                    if st.form_submit_button("🚀 लॉगिन करें (ट्रिप पैनल खोलें)" if is_hi else "🚀 Login to Trip Panel"):
                        if pin_in.strip() == drivers_db[ph_in]["pin"]:
                            st.session_state.logged_in_driver = drivers_db[ph_in]
                            st.rerun()
                        else:
                            st.error("❌ गलत PIN! कृपया सही 4 अंकों का PIN डालें।" if is_hi else "❌ Wrong PIN! Please try again.")
            else:
                st.info("📝 नया ड्राइवर रजिस्ट्रेशन (सिर्फ़ एक बार ₹99, फिर लोकल और चारधाम ट्रिप फ्री)" if is_hi else "📝 New Driver Registration (₹99 one-time)")
                with st.form("driver_reg_form"):
                    r_name = st.text_input("ड्राइवर का पूरा नाम" if is_hi else "Full Name", placeholder="मनोज जोशी")
                    r_addr = st.text_area("पूरा पता (गाँव / शहर / जिला)" if is_hi else "Full Address", placeholder="गाँव, पोस्ट, जिला...")
                    vt_opts = ["टैक्सी / शेयरिंग", "बाइक / स्कूटी"] if is_hi else ["Cab / Shared", "Bike / Scooty"]
                    r_vdisp = st.radio("गाड़ी का प्रकार:" if is_hi else "Vehicle Type:", vt_opts, horizontal=True)
                    r_vtype = "Bike / Scooty" if r_vdisp in ["बाइक / स्कूटी", "Bike / Scooty"] else "Cab / Shared"
                    r_veh = st.text_input("गाड़ी का नाम और नंबर" if is_hi else "Vehicle Name & Number", placeholder="Bolero UK 04 TA 9988")
                    r_dl = st.text_input("ड्राइविंग लाइसेंस नंबर (DL No.)" if is_hi else "Driving License Number", placeholder="UK0420200012345")
                    r_pin = st.text_input("🔐 अपना 4 अंकों का सीक्रेट PIN बनाएं (जैसे: 2580)" if is_hi else "🔐 Create 4-Digit Secret PIN", type="password", max_chars=4)

                    st.warning("💳 **रजिस्ट्रेशन शुल्क: ₹99 (केवल एक बार)**" if is_hi else "💳 **Registration Fee: ₹99 (One-Time)**")
                    paid_ok = st.checkbox("✅ मैंने ₹99 रजिस्ट्रेशन शुल्क जमा कर दिया है (Demo)" if is_hi else "✅ Paid ₹99 Registration Fee (Demo)")

                    if st.form_submit_button("🚀 रजिस्ट्रेशन पूरा करें और ट्रिप डालें" if is_hi else "🚀 Register & Open Trip Panel"):
                        if not (r_name and r_addr and r_veh and r_dl):
                            st.error("कृपया सभी जानकारी भरें।" if is_hi else "Please fill all fields.")
                        elif not (len(r_pin.strip()) == 4 and r_pin.strip().isdigit()):
                            st.error("कृपया 4 अंकों का नंबर वाला PIN बनाएं (जैसे 2580)।" if is_hi else "Please create a 4-digit numeric PIN.")
                        elif not paid_ok:
                            st.error("कृपया ₹99 शुल्क कन्फर्म करें।" if is_hi else "Please confirm ₹99 fee.")
                        else:
                            pin_clean = r_pin.strip()
                            new_drv_db = {
                                "name": r_name.strip(), "phone": ph_in, "address": r_addr.strip(),
                                "vehicle_type": r_vtype, "vehicle": r_veh.strip(),
                                "license": f"{r_dl.strip()} | PIN:{pin_clean}", "reg_paid": True
                            }
                            with st.spinner("रजिस्ट्रेशन सेव हो रहा है..."):
                                post_db({"action": "add_driver", "driver": new_drv_db})
                            new_drv_session = dict(new_drv_db)
                            new_drv_session["license"] = r_dl.strip()
                            new_drv_session["pin"] = pin_clean
                            st.session_state.logged_in_driver = new_drv_session
                            st.success("🎉 रजिस्ट्रेशन सफल! अब आप रोज़ फ्री में ट्रिप डाल सकते हैं।" if is_hi else "🎉 Registered!")
                            st.rerun()
        else:
            st.caption("नया रजिस्ट्रेशन करने या रोज़ की ट्रिप डालने के लिए ऊपर अपना 10 अंकों का मोबाइल नंबर लिखें।" if is_hi else "Enter your 10-digit mobile number.")

    else:
        drv = st.session_state.logged_in_driver
        c_top1, c_top2 = st.columns([3, 1])
        c_top1.success(f"👤 स्वागत है, **{drv['name']}** ({drv['vehicle']}) ✅" if is_hi else f"👤 Welcome, **{drv['name']}** ✅")
        if c_top2.button("🚪 लॉगआउट" if is_hi else "🚪 Logout"):
            st.session_state.logged_in_driver = None
            st.rerun()

        d1, d_cd, d_bk, d2 = st.tabs([
            "➕ लोकल ट्रिप" if is_hi else "➕ Local Trip",
            "🕉️ चारधाम ट्रिप (फ्री)" if is_hi else "🕉️ Char Dham (Free)",
            "📋 मेरी बुकिंग्स" if is_hi else "📋 My Bookings",
            "📡 लोकेशन / रद्द" if is_hi else "📡 Location / Cancel"
        ])

        with d1:
            s_search = st.text_input("आपकी गाड़ी अभी किस गाँव / बाज़ार में है? (खोजें)" if is_hi else "Current Village/Market", placeholder="जैसे: Kausani, Someshwar...")
            d_lat, d_lon, d_start = None, None, s_search.strip()
            if len(s_search.strip()) >= 3:
                s_res = search_uk_village(s_search)
                if s_res:
                    s_opts = {r["label"]: r for r in s_res}
                    s_pick = st.selectbox("अपना सही गाँव चुनें:" if is_hi else "Select village:", list(s_opts.keys()), key="drv_loc")
                    d_lat, d_lon, d_start = s_opts[s_pick]["lat"], s_opts[s_pick]["lon"], s_opts[s_pick]["name"]

            with st.form("add_trip"):
                d_stops = st.text_input("आगे के स्टॉप (कॉमा लगाकर लिखें)" if is_hi else "Route Stops (comma separated)", placeholder="जैसे: Someshwar, Kosi, Almora")
                c1, c2 = st.columns(2)
                d_time = c1.text_input("निकलने का समय" if is_hi else "Departure Time", placeholder="09:00 AM")
                d_fare = c2.number_input("आज का किराया (₹)" if is_hi else "Today's Fare (₹)", min_value=20, value=150, step=10)
                booked_cnt = st.slider("टैक्सी के लिए: कितनी सीटें पहले से बुक हैं?" if is_hi else "Seats already booked", 0, 6, 3)

                if st.form_submit_button("🚀 गाड़ी ऑनलाइन डालें" if is_hi else "🚀 Publish Trip"):
                    if d_stops or d_start:
                        s_list = [x.strip() for x in d_stops.split(",") if x.strip()]
                        if d_start and (not s_list or d_start.lower() != s_list[0].lower()):
                            s_list.insert(0, d_start)
                        if drv["vehicle_type"] == "Bike / Scooty":
                            s_map = {"Pillion-Seat": "Available"}
                        else:
                            names = ["Front-1", "Mid-1", "Mid-2", "Mid-3", "Back-1", "Back-2", "Back-3"]
                            s_map = {s: ("Booked" if i < booked_cnt else "Available") for i, s in enumerate(names)}
                        new_tid = (max([t["id"] for t in trips_db]) + 1) if trips_db else 1
                        new_trip = {
                            "id": new_tid, "driver": drv["name"], "phone": drv["phone"],
                            "vehicle_type": drv["vehicle_type"], "vehicle": drv["vehicle"], "stops": s_list,
                            "lat": d_lat, "lon": d_lon, "time": d_time, "full_fare": d_fare, "seats": s_map
                        }
                        with st.spinner("गाड़ी ऑनलाइन डाली जा रही है..."):
                            post_db({"action": "add_trip", "trip": new_trip})
                        st.success("✅ आपकी लोकल गाड़ी लाइव हो गई है!" if is_hi else "✅ Trip is now live!")
                        st.rerun()
                    else:
                        st.error("कृपया अपना गाँव या रूट ज़रूर लिखें।" if is_hi else "Please enter route stops.")

        with d_cd:
            st.subheader("🕉️ चारधाम यात्रा के लिए अपनी गाड़ी डालें (बिल्कुल फ्री)" if is_hi else "🕉️ Post Your Cab for Char Dham (100% Free)")
            st.caption("यहाँ डाली गई गाड़ी यात्रियों को '🕉️ चारधाम यात्रा' टैब में दिखेगी। बुकिंग आने पर आपको '📋 मेरी बुकिंग्स' में दिखेगा।" if is_hi else "Your listing will appear in the Char Dham tab. Confirmed bookings show up in My Bookings.")
            with st.form("add_cd_trip"):
                cc1, cc2 = st.columns(2)
                cd_p = cc1.selectbox("कहाँ से पिकअप करेंगे?" if is_hi else "Pickup City:", ["Haridwar", "Rishikesh", "Dehradun", "Delhi / NCR", "Kathgodam / Haldwani"])
                cd_d = cc2.selectbox("कौन से धाम की यात्रा?" if is_hi else "Dham Package:", [
                    "Poora Char Dham (4 Dham)", "Do Dham (Kedarnath + Badrinath)",
                    "Kedarnath Dham", "Badrinath Dham", "Gangotri / Yamunotri"
                ])
                cd_mode = st.radio("बुकिंग का प्रकार:" if is_hi else "Booking Type:", ["पूरी गाड़ी (Full Cab)", "शेयरिंग सीट (Shared Seats)"], horizontal=True)
                cc3, cc4 = st.columns(2)
                cd_days = cc3.text_input("दिन / उपलब्धता" if is_hi else "Duration / Availability", placeholder="जैसे: 9-10 दिन (मई-जून)")
                cd_rate = cc4.number_input("कुल किराया / पैकेज रेट (₹)" if is_hi else "Package Rate (₹)", min_value=500, value=25000, step=500)

                if st.form_submit_button("🕉️ चारधाम के लिए गाड़ी ऑनलाइन डालें" if is_hi else "🕉️ Publish Char Dham Cab", type="primary"):
                    new_tid = (max([t["id"] for t in trips_db]) + 1) if trips_db else 1
                    if "Full Cab" in cd_mode:
                        cd_seats = {"Full-Cab": "Available"}
                    else:
                        cd_seats = {f"Seat-{i}": "Available" for i in range(1, 7)}
                    new_cd_trip = {
                        "id": new_tid, "driver": drv["name"], "phone": drv["phone"],
                        "vehicle_type": "CharDham", "vehicle": drv["vehicle"],
                        "stops": [cd_p, cd_d], "lat": "", "lon": "",
                        "time": cd_days.strip() or "उपलब्ध (Available)",
                        "full_fare": cd_rate, "seats": cd_seats
                    }
                    with st.spinner("चारधाम ट्रिप ऑनलाइन डाली जा रही है..."):
                        post_db({"action": "add_trip", "trip": new_cd_trip})
                    st.success("✅ आपकी गाड़ी चारधाम यात्रा के लिए लाइव हो गई है!" if is_hi else "✅ Your cab is now live for Char Dham!")
                    st.rerun()

        with d_bk:
            st.subheader("📋 आपकी गाड़ी की सवारियाँ (लोकल + चारधाम)" if is_hi else "📋 Your Bookings (Local + Char Dham)")
            drv_bookings = [b for b in bookings_db if b["phone"] == drv["phone"]]
            conf_list = [b for b in drv_bookings if b["status"] == "Confirmed"]
            canc_list = [b for b in drv_bookings if b["status"] == "Cancelled"]

            m1, m2 = st.columns(2)
            m1.metric("✅ कन्फर्म बुकिंग्स" if is_hi else "✅ Confirmed", len(conf_list))
            m2.metric("❌ रद्द की गई" if is_hi else "❌ Cancelled", len(canc_list))

            if not drv_bookings:
                st.info("अभी आपकी गाड़ी के लिए कोई बुकिंग नहीं आई है।" if is_hi else "No bookings yet.")
            else:
                for b in reversed(drv_bookings):
                    t_info = trips_by_id.get(b["trip_id"], {})
                    t_time = t_info.get("time", "")
                    ph_match = re.search(r"(\d{10})", b["passenger"])
                    p_ph = ph_match.group(1) if ph_match else ""
                    p_wa = f"https://wa.me/91{p_ph}" if p_ph else ""
                    with st.container(border=True):
                        if b["status"] == "Cancelled":
                            st.error(f"❌ सवारी ने रद्द कर दिया — **{b['seat']}** | {b['passenger']}" if is_hi else f"❌ Cancelled — **{b['seat']}** | {b['passenger']}")
                        else:
                            st.success(f"✅ कन्फर्म — **{b['seat']}** | 🕒 {t_time}" if is_hi else f"✅ Confirmed — **{b['seat']}** | 🕒 {t_time}")
                            st.write(f"👤 **सवारी:** {b['passenger']}")
                            st.write(f"🛣️ **रूट:** {b['route']} | 💰 **किराया:** ₹{b['fare']}")
                            if p_wa:
                                st.link_button(
                                    f"💬 सवारी को व्हाट्सएप करें ({p_ph})" if is_hi else f"💬 WhatsApp Passenger ({p_ph})",
                                    p_wa,
                                    use_container_width=True
                                )

        with d2:
            my_trips = [t for t in trips_db if t["status"] == "Active" and t["phone"] == drv["phone"]]
            if not my_trips:
                st.info("आपकी अभी कोई सक्रिय ट्रिप नहीं है।" if is_hi else "No active trips.")
            else:
                d_map = {f"{'🕉️ ' if t['vehicle_type']=='CharDham' else '🚕 '}{t['vehicle']} ({t['stops'][0]} ➔ {t['stops'][-1]})": t for t in my_trips if t["stops"]}
                st_trip = d_map[st.selectbox("अपनी ट्रिप चुनें:" if is_hi else "Select Trip:", list(d_map.keys()))]
                if st_trip["vehicle_type"] != "CharDham":
                    n_stop = st.selectbox("अभी कहाँ पहुँचे हैं?" if is_hi else "Current Location:", st_trip["stops"], index=st_trip["current_stop_idx"])
                    n_delay = st.radio("क्या गाड़ी लेट है?" if is_hi else "Delay:", [0, 10, 20, 30], format_func=lambda x: ("समय पर" if is_hi else "On Time") if x == 0 else f"+{x} min", horizontal=True)
                    n_reason = st.text_input("लेट होने का कारण" if is_hi else "Delay Reason", value=st_trip["delay_reason"])

                    col_u, col_c = st.columns(2)
                    if col_u.button("📡 लोकेशन अपडेट करें" if is_hi else "📡 Update Location"):
                        with st.spinner("अपडेट हो रहा है..."):
                            post_db({
                                "action": "update_trip", "id": st_trip["id"],
                                "current_stop_idx": st_trip["stops"].index(n_stop),
                                "delay_mins": n_delay,
                                "delay_reason": ("समय पर" if is_hi else "On Time") if n_delay == 0 else n_reason
                            })
                        st.success("✅ लोकेशन अपडेट हो गई!")
                        st.rerun()
                    if col_c.button("🚫 पूरी ट्रिप रद्द करें" if is_hi else "🚫 Cancel Trip"):
                        with st.spinner("रद्द हो रहा है..."):
                            post_db({"action": "update_trip", "id": st_trip["id"], "status": "Cancelled"})
                        st.error("ट्रिप रद्द कर दी गई है।")
                        st.rerun()
                else:
                    st.info("यह आपकी सक्रिय चारधाम ट्रिप है। अगर इसे हटाना हो तो नीचे क्लिक करें:" if is_hi else "Active Char Dham listing:")
                    if st.button("🚫 चारधाम ट्रिप हटाएं" if is_hi else "🚫 Remove Char Dham Trip"):
                        with st.spinner("हटाया जा रहा है..."):
                            post_db({"action": "update_trip", "id": st_trip["id"], "status": "Cancelled"})
                        st.error("चारधाम ट्रिप हटा दी गई है।")
                        st.rerun()

# ==========================================
# FOOTER: 24x7 HELP & SUPPORT + TERMS
# ==========================================
st.divider()
with st.expander("🆘 मदद / Help & Support (24x7)"):
    st.caption(
        "किसी भी शिकायत, गाड़ी में छूटे सामान, या ड्राइवर PIN रीसेट के लिए नीचे क्लिक करें:"
        if is_hi else
        "For complaints, lost items, or Driver PIN reset, contact DevBhoomi Support:"
    )
    sup_msg = quote("नमस्ते DevBhoomi Ride Support, मुझे मदद चाहिए:")
    sc1, sc2 = st.columns(2)
    sc1.link_button(
        "💬 DevBhoomi Support (WhatsApp)" if is_hi else "💬 WhatsApp Support",
        f"https://wa.me/{SUPPORT_WHATSAPP}?text={sup_msg}",
        type="primary",
        use_container_width=True
    )
    sc2.link_button(
        "🚨 Emergency Police / SDRF (112)" if is_hi else "🚨 Emergency SOS (112)",
        "tel:112",
        use_container_width=True
    )

with st.expander("📜 नियम और शर्तें / Terms & Privacy Policy"):
    if is_hi:
        st.markdown("""
**📜 नियम और शर्तें (Terms & Conditions):**
1. **प्लेटफ़ॉर्म की भूमिका:** DevBhoomi Ride केवल एक ऑनलाइन बुकिंग प्लेटफ़ॉर्म है जो यात्रियों और लोकल ड्राइवरों को आपस में जोड़ता है। गाड़ी की कंडीशन, वैध लाइसेंस (DL), कागज़ात और सुरक्षित ड्राइविंग की पूरी ज़िम्मेदारी संबंधित ड्राइवर की होगी।
2. **किराया और यात्रा नियम:** लोकल या चारधाम यात्रा का किराया, टोल, पार्किंग और पहाड़ों पर चढ़ाई के समय AC बंद रहने जैसे नियम यात्री और ड्राइवर के बीच लागू होंगे।
3. **रद्द करना (Cancellation):** सीट या ट्रिप रद्द करने पर कृपया ऐप में तुरंत रद्द करें और सामने वाले को व्हाट्सएप पर सूचित करें। बार-बार फर्जी बुकिंग करने पर नंबर ब्लॉक किया जा सकता है।
4. **सुरक्षा और सामान:** यात्रा के दौरान अपने कीमती सामान की ज़िम्मेदारी यात्री की स्वयं की होगी। बाइक/स्कूटी राइड के लिए हेलमेट अनिवार्य है। किसी भी आपात स्थिति में **112** पर कॉल करें।

---
**🔒 गोपनीयता नीति (Privacy Policy):**
1. **डेटा संग्रह:** हम केवल वही जानकारी लेते हैं जो बुकिंग के लिए ज़रूरी है (नाम, मोबाइल नंबर, और ड्राइवरों के लिए गाड़ी नंबर, पता व लाइसेंस)।
2. **नंबर की सुरक्षा:** यात्री और ड्राइवर का मोबाइल नंबर केवल बुकिंग कन्फर्म होने के बाद ही एक-दूसरे को दिखता है। हम आपका डेटा किसी भी बाहरी कंपनी को नहीं बेचते।
3. **डेटा हटाना:** यदि कोई ड्राइवर या यात्री अपना डेटा हटवाना चाहता है, तो ऊपर दिए गए Support WhatsApp पर संदेश भेजकर हटवा सकता है।
        """)
    else:
        st.markdown("""
**📜 Terms & Conditions:**
1. **Platform Role:** DevBhoomi Ride is only an online booking platform connecting passengers and local drivers. Vehicle condition, valid Driving License, documents, and safe driving are the sole responsibility of the driver.
2. **Fare & Travel Rules:** Local or Char Dham fares, tolls, parking, and mountain rules (such as AC off on steep climbs) apply directly between the passenger and driver.
3. **Cancellations:** If cancelling a seat or trip, please cancel immediately in the app and inform via WhatsApp. Repeated fake bookings may lead to number blocking.
4. **Safety & Luggage:** Passengers are responsible for their own luggage and valuables. Helmets are mandatory for Bike/Scooty rides. Call **112** in any emergency.

---
**🔒 Privacy Policy:**
1. **Data Collection:** We only collect details required for booking (Name, Mobile Number, and Vehicle/Address/DL details for drivers).
2. **Number Privacy:** Driver and passenger contact numbers are shared with each other only after booking confirmation. We never sell user data to third parties.
3. **Data Removal:** Any driver or passenger can request deletion of their data anytime via the Support WhatsApp button above.
        """)
