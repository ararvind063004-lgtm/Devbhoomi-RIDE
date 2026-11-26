import streamlit as st
import requests
import math
import json
from urllib.parse import quote

st.set_page_config(page_title="DevBhoomi Ride", page_icon="🏔️", layout="centered")

DB_URL = "https://script.google.com/macros/s/AKfycby3A2XJ0_hrgcs0IRy-pnJzQWmXmwrndsQXZEN73EjNoKKlSIW83dxnjqGp4L6yZ15heQ/exec"

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
                    drivers[ph] = {
                        "phone": ph, "name": str(d.get("name", "")),
                        "address": str(d.get("address", "")),
                        "vehicle_type": str(d.get("vehicle_type", "Cab / Shared")),
                        "vehicle": str(d.get("vehicle", "")),
                        "license": str(d.get("license", "")), "reg_paid": True
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
                msg = quote(f"Namaste {b.get('driver','')} ji, DevBhoomi Ride par {b.get('seat','')} book ki hai ({b.get('route','')}). Naam: {b.get('passenger','')}")
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
drivers_db, trips_db, bookings_db = load_db()
active_trips = [t for t in trips_db if t["status"] == "Active"]
trips_by_id = {t["id"]: t for t in trips_db}

if "logged_in_driver" not in st.session_state:
    st.session_state.logged_in_driver = None
if "last_p_phone" not in st.session_state:
    st.session_state.last_p_phone = ""

# --- LANGUAGE SWITCH & HEADER ---
c_lang, c_ref = st.columns([3, 1])
lang = c_lang.radio("🌐 भाषा चुनें / Language:", ["हिंदी", "English"], horizontal=True)
is_hi = (lang == "हिंदी")
if c_ref.button("🔄 रिफ्रेश" if is_hi else "🔄 Refresh"):
    load_db.clear()
    st.rerun()

st.title("🏔️ देवभूमि राइड" if is_hi else "🏔️ DevBhoomi Ride")
st.caption("उत्तराखंड के हर गाँव से बाज़ार तक — टैक्सी, बाइक और स्कूटी" if is_hi else "From every Uttarakhand village to city — Cab, Bike & Scooty")

t1, t_my, t2, t3 = st.tabs([
    "🔍 सीट बुक करें" if is_hi else "🔍 Book Ride",
    "🎫 मेरी बुकिंग" if is_hi else "🎫 My Bookings",
    "📍 लाइव लोकेशन" if is_hi else "📍 Live Track",
    "👨‍✈️ ड्राइवर पैनल" if is_hi else "👨‍✈️ Driver Panel"
])

# ==========================================
# TAB 1: PASSENGER SEARCH & BOOKING
# ==========================================
with t1:
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
    for trip in active_trips:
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
                                new_bid = (max([b["bid"] for b in bookings_db]) + 1) if bookings_db else 1
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
                                st.session_state.last_p_phone = p_phone.strip()
                                st.success("🎉 बुकिंग कन्फर्म हो गई! ऊपर '🎫 मेरी बुकिंग' टैब में अपनी टिकट और ड्राइवर का नंबर कभी भी देख सकते हैं।" if is_hi else "🎉 Confirmed! Check '🎫 My Bookings' anytime.")
                                st.rerun()

# ==========================================
# TAB 2: MY BOOKINGS (CHECK ANYTIME BY PHONE)
# ==========================================
with t_my:
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
                        st.error(f"❌ रद्द की गई — {b['vehicle']} | सीट: {b['seat']}" if is_hi else f"❌ Cancelled — {b['vehicle']} | Seat: {b['seat']}")
                    else:
                        if t_status == "Cancelled":
                            st.warning("⚠️ ध्यान दें: ड्राइवर ने यह ट्रिप रद्द कर दी है।" if is_hi else "⚠️ Note: Driver cancelled this trip.")
                        else:
                            st.success(f"✅ कन्फर्म टिकट — सीट: **{b['seat']}** | 🕒 समय: **{t_time}**" if is_hi else f"✅ Confirmed — Seat: **{b['seat']}** | 🕒 Time: **{t_time}**")
                        st.write(f"🚕 **{b['vehicle']}** | 🛣️ {b['route']}")
                        st.write(f"💰 ड्राइवर को देना है: **₹{b['fare']}** | बुकिंग शुल्क: ₹{b['fee']}" if is_hi else f"💰 Pay Driver: **₹{b['fare']}** | Fee: ₹{b['fee']}")
                        st.markdown(f"👤 **{b['driver']}** | 📞 **{b['phone']}** | [💬 व्हाट्सएप]({b['wa']})" if is_hi else f"👤 **{b['driver']}** | 📞 **{b['phone']}** | [💬 WhatsApp]({b['wa']})")
                        if st.button("❌ सीट रद्द करें" if is_hi else "❌ Cancel Seat", key=f"cnl_{b['bid']}"):
                            with st.spinner("रद्द हो रहा है..."):
                                post_db({"action": "cancel_booking", "bid": b["bid"]})
                                if b["trip_id"] in trips_by_id:
                                    upd_seats = dict(trips_by_id[b["trip_id"]]["seats"])
                                    upd_seats[b["seat"]] = "Available"
                                    post_db({"action": "update_trip", "id": b["trip_id"], "seats": upd_seats})
                            st.rerun()
    else:
        st.caption("अपनी पुरानी या कल की बुकिंग देखने के लिए ऊपर 10 अंकों का मोबाइल नंबर डालें।" if is_hi else "Enter your 10-digit mobile number to view your tickets anytime.")

# ==========================================
# TAB 3: LIVE TRACKING
# ==========================================
with t2:
    st.subheader("📍 गाड़ी अभी कहाँ पहुँची है?" if is_hi else "📍 Live Tracking")
    if not active_trips:
        st.info("अभी कोई सक्रिय ट्रिप नहीं है।" if is_hi else "No active trips.")
    else:
        t_map = {f"{t['vehicle']} ({t['stops'][0]} ➔ {t['stops'][-1]})": t for t in active_trips if t["stops"]}
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
# TAB 4: DRIVER PANEL (LIVE GOOGLE SHEETS)
# ==========================================
with t3:
    if st.session_state.logged_in_driver is None:
        st.subheader("👨‍✈️ ड्राइवर रजिस्ट्रेशन / प्रवेश" if is_hi else "👨‍✈️ Driver Registration / Access")
        ph_in = st.text_input(
            "अपना 10 अंकों का मोबाइल नंबर डालें:" if is_hi else "Enter your 10-digit Mobile Number:",
            placeholder="जैसे: 9876543210"
        ).strip()

        if len(ph_in) >= 10:
            if ph_in in drivers_db:
                st.success("✅ आपका नंबर पहले से रजिस्टर्ड है!" if is_hi else "✅ Already registered!")
                if st.button("🚀 आगे बढ़ें (ट्रिप पैनल खोलें)" if is_hi else "🚀 Continue to Trip Panel"):
                    st.session_state.logged_in_driver = drivers_db[ph_in]
                    st.rerun()
            else:
                st.info("📝 नया ड्राइवर रजिस्ट्रेशन (सिर्फ़ एक बार ₹99, फिर रोज़ की ट्रिप फ्री)" if is_hi else "📝 New Driver Registration (₹99 one-time)")
                with st.form("driver_reg_form"):
                    r_name = st.text_input("ड्राइवर का पूरा नाम" if is_hi else "Full Name", placeholder="मनोज जोशी")
                    r_addr = st.text_area("पूरा पता (गाँव / शहर / जिला)" if is_hi else "Full Address", placeholder="गाँव, पोस्ट, जिला...")
                    vt_opts = ["टैक्सी / शेयरिंग", "बाइक / स्कूटी"] if is_hi else ["Cab / Shared", "Bike / Scooty"]
                    r_vdisp = st.radio("गाड़ी का प्रकार:" if is_hi else "Vehicle Type:", vt_opts, horizontal=True)
                    r_vtype = "Bike / Scooty" if r_vdisp in ["बाइक / स्कूटी", "Bike / Scooty"] else "Cab / Shared"
                    r_veh = st.text_input("गाड़ी का नाम और नंबर" if is_hi else "Vehicle Name & Number", placeholder="Bolero UK 04 TA 9988")
                    r_dl = st.text_input("ड्राइविंग लाइसेंस नंबर (DL No.)" if is_hi else "Driving License Number", placeholder="UK0420200012345")

                    st.warning("💳 **रजिस्ट्रेशन शुल्क: ₹99 (केवल एक बार)**" if is_hi else "💳 **Registration Fee: ₹99 (One-Time)**")
                    paid_ok = st.checkbox("✅ मैंने ₹99 रजिस्ट्रेशन शुल्क जमा कर दिया है (Demo)" if is_hi else "✅ Paid ₹99 Registration Fee (Demo)")

                    if st.form_submit_button("🚀 रजिस्ट्रेशन पूरा करें और ट्रिप डालें" if is_hi else "🚀 Register & Open Trip Panel"):
                        if not (r_name and r_addr and r_veh and r_dl):
                            st.error("कृपया सभी जानकारी भरें।" if is_hi else "Please fill all fields.")
                        elif not paid_ok:
                            st.error("कृपया ₹99 शुल्क कन्फर्म करें।" if is_hi else "Please confirm ₹99 fee.")
                        else:
                            new_drv = {
                                "name": r_name.strip(), "phone": ph_in, "address": r_addr.strip(),
                                "vehicle_type": r_vtype, "vehicle": r_veh.strip(), "license": r_dl.strip(), "reg_paid": True
                            }
                            with st.spinner("रजिस्ट्रेशन सेव हो रहा है..."):
                                post_db({"action": "add_driver", "driver": new_drv})
                            st.session_state.logged_in_driver = new_drv
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

        d1, d2 = st.tabs([
            "➕ आज की ट्रिप डालें (फ्री)" if is_hi else "➕ Add Today's Trip (Free)",
            "📡 लोकेशन अपडेट / ट्रिप रद्द करें" if is_hi else "📡 Update Location / Cancel"
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
                        st.success("✅ आपकी गाड़ी लाइव हो गई है!" if is_hi else "✅ Trip is now live!")
                        st.rerun()
                    else:
                        st.error("कृपया अपना गाँव या रूट ज़रूर लिखें।" if is_hi else "Please enter route stops.")

        with d2:
            my_trips = [t for t in active_trips if t["phone"] == drv["phone"]]
            if not my_trips:
                st.info("आपकी अभी कोई सक्रिय ट्रिप नहीं है।" if is_hi else "No active trips.")
            else:
                d_map = {f"{t['vehicle']} ({t['stops'][0]} ➔ {t['stops'][-1]})": t for t in my_trips if t["stops"]}
                st_trip = d_map[st.selectbox("अपनी ट्रिप चुनें:" if is_hi else "Select Trip:", list(d_map.keys()))]
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
