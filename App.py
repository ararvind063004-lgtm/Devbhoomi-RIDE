import streamlit as st
from urllib.parse import quote

st.set_page_config(page_title="DevBhoomi Ride", page_icon="🏔️", layout="centered")

# --- LANGUAGE SWITCH ---
lang = st.radio("🌐 Bhasha / Language:", ["Hindi (Hinglish)", "English"], horizontal=True)
is_hi = (lang == "Hindi (Hinglish)")

# --- INITIAL DEMO DATA ---
if "trips" not in st.session_state:
    st.session_state.trips = [
        {
            "id": 1,
            "driver": "Ramesh Bisht",
            "phone": "9876543210",
            "vehicle_type": "Cab / Shared",
            "vehicle": "Mahindra Bolero (UK 04 TA 4521)",
            "stops": ["Haldwani", "Kathgodam", "Bhimtal", "Bhowali", "Kainchi Dham", "Almora"],
            "time": "08:30 AM",
            "full_fare": 250,
            "current_stop_idx": 1,
            "delay_mins": 10,
            "delay_reason": "Kathgodam mein sawaari baitha rahe hain",
            "status": "Active",
            "seats": {
                "Front-1": "Booked",
                "Mid-1": "Booked", "Mid-2": "Booked", "Mid-3": "Booked",
                "Back-1": "Booked", "Back-2": "Booked", "Back-3": "Available"
            }
        },
        {
            "id": 2,
            "driver": "Suresh Negi",
            "phone": "9811223344",
            "vehicle_type": "Cab / Shared",
            "vehicle": "Toyota Innova (UK 07 TB 8890)",
            "stops": ["Dehradun", "Rishikesh", "Haridwar", "Roorkee", "Meerut", "Delhi (ISBT)"],
            "time": "09:00 AM",
            "full_fare": 700,
            "current_stop_idx": 2,
            "delay_mins": 0,
            "delay_reason": "On Time",
            "status": "Active",
            "seats": {
                "Front-1": "Booked",
                "Mid-1": "Booked", "Mid-2": "Available", "Mid-3": "Booked",
                "Back-1": "Booked", "Back-2": "Available", "Back-3": "Booked"
            }
        },
        {
            "id": 3,
            "driver": "Amit Rawat",
            "phone": "9756001122",
            "vehicle_type": "Bike / Scooty",
            "vehicle": "Honda Activa (UK 04 AB 2233)",
            "stops": ["Haldwani", "Kathgodam", "Bhimtal", "Bhowali"],
            "time": "Abhi Available",
            "full_fare": 80,
            "current_stop_idx": 0,
            "delay_mins": 0,
            "delay_reason": "On Time",
            "status": "Active",
            "seats": {"Pillion-Seat": "Available"}
        }
    ]

if "bookings" not in st.session_state:
    st.session_state.bookings = []

active_trips = [t for t in st.session_state.trips if t["status"] == "Active"]
all_stops = sorted(list({stop for t in active_trips for stop in t["stops"]}))

# --- HEADER ---
st.title("🏔️ DevBhoomi Ride")
st.caption("Uttarakhand Cab, Bike/Scooty, Local Ride, Delhi & Char Dham" if is_hi else "Uttarakhand Cab, Bike/Scooty, Local, Delhi & Char Dham")

t1, t2, t3 = st.tabs([
    "🔍 Ride Book Karo" if is_hi else "🔍 Book Ride",
    "📍 Live Track",
    "👨‍✈️ Driver Panel"
])

# ==========================================
# TAB 1: PASSENGER SEARCH & BOOKING
# ==========================================
with t1:
    v_filter = st.radio(
        "Kya chahiye?" if is_hi else "Vehicle Type:",
        ["Sabhi", "Cab / Shared", "Bike / Scooty"],
        horizontal=True
    )
    c1, c2 = st.columns(2)
    with c1:
        pickup = st.selectbox("Kahan se? (Pickup)" if is_hi else "Pickup", ["Sabhi Locations"] + all_stops)
    with c2:
        drop = st.selectbox("Kahan jana hai? (Drop)" if is_hi else "Drop", ["Sabhi Locations"] + all_stops)

    matched = []
    for trip in active_trips:
        if v_filter != "Sabhi" and trip["vehicle_type"] != v_filter:
            continue
        stops = trip["stops"]
        if pickup == "Sabhi Locations" and drop == "Sabhi Locations":
            matched.append((trip, trip["full_fare"], stops[0], stops[-1]))
        elif pickup != "Sabhi Locations" and drop != "Sabhi Locations":
            if pickup in stops and drop in stops and stops.index(pickup) < stops.index(drop):
                ratio = (stops.index(drop) - stops.index(pickup)) / max(1, len(stops) - 1)
                min_f = 20 if trip["vehicle_type"] == "Bike / Scooty" else 30
                calc_fare = max(min_f, int(round((trip["full_fare"] * ratio) / 10) * 10))
                matched.append((trip, calc_fare, pickup, drop))
        elif pickup != "Sabhi Locations" and pickup in stops[:-1]:
            matched.append((trip, trip["full_fare"], pickup, stops[-1]))
        elif drop != "Sabhi Locations" and drop in stops[1:]:
            matched.append((trip, trip["full_fare"], stops[0], drop))

    matched.sort(key=lambda x: (sum(1 for v in x[0]["seats"].values() if v == "Available") == 0,
                                sum(1 for v in x[0]["seats"].values() if v == "Available")))

    if not matched:
        st.warning("Is route par abhi koi gaadi nahi mili." if is_hi else "No rides found on this route.")
    else:
        for trip, fare, p_stop, d_stop in matched:
            avail_seats = [s for s, status in trip["seats"].items() if status == "Available"]
            avail_count = len(avail_seats)
            fee = max(5, int(round((fare * 0.10) / 5) * 5))

            with st.container(border=True):
                if trip["vehicle_type"] == "Bike / Scooty":
                    st.info("🏍️ Bike / Scooty — 1 Sawaari, Halka Bag & Helmet Zaroori")
                elif avail_count == 1:
                    st.error("🔥 Sirf 1 Seat Bachi Hai — Turant Niklegi!" if is_hi else "🔥 Only 1 Seat Left!")
                elif avail_count == 2:
                    st.warning("⚡ Sirf 2 Seats Bachi Hain!" if is_hi else "⚡ Only 2 Seats Left!")
                elif avail_count == 0:
                    st.info("❌ Full Ho Chuki Hai" if is_hi else "❌ Full")
                else:
                    st.success(f"✅ {avail_count} Seats Available")

                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**{trip['vehicle']}**")
                    st.write(f"🛣️ **{p_stop} ➔ {d_stop}**")
                    st.caption(f"🕒 {trip['time']} | 👤 {trip['driver']} | 📞 🔒 *Booking par unlock hoga*")
                with col_b:
                    st.markdown(f"### ₹{fare}")
                    st.caption(f"+ ₹{fee} fee")

                if avail_count > 0:
                    with st.expander("💺 Seat Choose Karo / Book Karo" if is_hi else "💺 Select Seat & Book"):
                        if trip["vehicle_type"] == "Cab / Shared":
                            st.write("🟩 Available   |   🟥 Booked")
                            r1c1, r1c2 = st.columns(2)
                            r1c1.button("🛞 Driver", disabled=True, key=f"d_{trip['id']}")
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

                        chosen_seat = st.selectbox("Seat Chunein:" if is_hi else "Choose Seat:", avail_seats, key=f"sel_{trip['id']}")
                        p_name = st.text_input("Aapka Naam" if is_hi else "Your Name", key=f"nm_{trip['id']}")
                        p_phone = st.text_input("Aapka Mobile Number" if is_hi else "Mobile Number", key=f"ph_{trip['id']}")

                        if st.button(f"✅ Confirm Karo (Kiraya ₹{fare} + Fee ₹{fee})", key=f"bk_{trip['id']}"):
                            if not p_name or not p_phone:
                                st.error("Naam aur Mobile Number daalna zaroori hai.")
                            else:
                                trip["seats"][chosen_seat] = "Booked"
                                msg = quote(f"Namaste {trip['driver']} ji, DevBhoomi Ride par {chosen_seat} book ki hai ({p_stop} se {d_stop}). Naam: {p_name}, Phone: {p_phone}")
                                st.session_state.bookings.append({
                                    "bid": len(st.session_state.bookings) + 1,
                                    "trip_id": trip["id"], "passenger": p_name, "seat": chosen_seat,
                                    "vehicle": trip["vehicle"], "route": f"{p_stop} ➔ {d_stop}",
                                    "fare": fare, "fee": fee, "driver": trip["driver"],
                                    "phone": trip["phone"], "wa": f"https://wa.me/91{trip['phone']}?text={msg}",
                                    "status": "Confirmed"
                                })
                                st.success("🎉 Booking Confirm! Driver ka number neeche unlock ho gaya hai.")
                                st.rerun()

    # Confirmed Bookings + Cancel Option
    if st.session_state.bookings:
        st.subheader("🔓 Aapki Bookings (Driver Details)")
        for b in reversed(st.session_state.bookings):
            with st.container(border=True):
                if b["status"] == "Cancelled":
                    st.error(f"❌ Cancelled — {b['vehicle']} | Seat: {b['seat']}")
                else:
                    st.write(f"**{b['vehicle']}** | Seat: **{b['seat']}** | {b['route']}")
                    st.write(f"Driver ko dena hai: **₹{b['fare']}** | Platform Fee: ₹{b['fee']}")
                    st.markdown(f"👤 **{b['driver']}** | 📞 **{b['phone']}** | [💬 WhatsApp]({b['wa']})")
                    if st.button("❌ Seat Cancel Karein", key=f"cnl_{b['bid']}"):
                        b["status"] = "Cancelled"
                        for t in st.session_state.trips:
                            if t["id"] == b["trip_id"]:
                                t["seats"][b["seat"]] = "Available"
                        st.warning("Seat cancel ho gayi aur dobara available kar di gayi hai.")
                        st.rerun()

# ==========================================
# TAB 2: LIVE TRACKING
# ==========================================
with t2:
    st.subheader("📍 Gaadi Kahan Pahunchi Hai?" if is_hi else "📍 Live Tracking")
    if not active_trips:
        st.info("Abhi koi active trip nahi hai.")
    else:
        t_map = {f"{t['vehicle']} ({t['stops'][0]} ➔ {t['stops'][-1]})": t for t in active_trips}
        tr = t_map[st.selectbox("Gaadi Chunein:", list(t_map.keys()))]
        u_stop = st.selectbox("Aap kis stop par hain?", tr["stops"], index=min(2, len(tr["stops"]) - 1))

        c_idx, u_idx, delay = tr["current_stop_idx"], tr["stops"].index(u_stop), tr["delay_mins"]
        if delay > 0:
            st.warning(f"⚠️ **{delay} min late** — *{tr['delay_reason']}*")
        else:
            st.success("✅ Right Time par chal rahi hai!")

        if u_idx < c_idx:
            st.error(f"❌ Gaadi **{u_stop}** se nikal chuki hai.")
        elif u_idx == c_idx:
            st.success(f"🚕 Gaadi abhi **{u_stop}** par pahunch chuki hai!")
        else:
            st.info(f"🕒 **{u_stop}** par lagbhag **{(u_idx - c_idx) * 15 + delay} minute** mein pahunchegi.")

        for idx, s in enumerate(tr["stops"]):
            if idx < c_idx:
                st.markdown(f"✅ ~~{s}~~")
            elif idx == c_idx:
                st.markdown(f"🚕 **{s} ⬅️ ABHI YAHAN HAI**")
            elif idx == u_idx:
                st.markdown(f"📍 **{s} (Aapka Stop)**")
            else:
                st.markdown(f"⚪ {s}")

# ==========================================
# TAB 3: DRIVER PANEL
# ==========================================
with t3:
    d1, d2 = st.tabs(["➕ Nayi Trip Daalein", "📡 Location / Cancel Trip"])

    with d1:
        st.subheader("Driver Bhai apni gaadi aur aaj ka kiraya daalein" if is_hi else "Add New Trip")
        with st.form("add_trip"):
            v_type = st.radio("Gaadi ka Type:", ["Cab / Shared", "Bike / Scooty"], horizontal=True)
            d_name = st.text_input("Aapka Naam", placeholder="Manoj Joshi")
            d_phone = st.text_input("Mobile Number", placeholder="10 digit number")
            d_veh = st.text_input("Gaadi ka Naam aur Number", placeholder="Bolero UK 04 TA 9988 ya Activa UK 04 AB 1122")
            d_stops = st.text_input("Route ke stops (comma lagakar)", placeholder="Haldwani, Bhimtal, Bhowali, Almora")
            c1, c2 = st.columns(2)
            d_time = c1.text_input("Nikalne ka Time", placeholder="09:00 AM")
            d_fare = c2.number_input("Aaj ka Kiraya (₹)", min_value=20, value=200, step=10)
            booked_cnt = st.slider("Cab ke liye: Kitni seats pehle se book hain?", 0, 6, 3)

            if st.form_submit_button("🚀 Gaadi Live Karein"):
                if d_name and d_phone and d_veh and d_stops:
                    s_list = [x.strip() for x in d_stops.split(",") if x.strip()]
                    if v_type == "Bike / Scooty":
                        s_map = {"Pillion-Seat": "Available"}
                    else:
                        names = ["Front-1", "Mid-1", "Mid-2", "Mid-3", "Back-1", "Back-2", "Back-3"]
                        s_map = {s: ("Booked" if i < booked_cnt else "Available") for i, s in enumerate(names)}
                    st.session_state.trips.append({
                        "id": len(st.session_state.trips) + 1, "driver": d_name, "phone": d_phone,
                        "vehicle_type": v_type, "vehicle": d_veh, "stops": s_list, "time": d_time,
                        "full_fare": d_fare, "current_stop_idx": 0, "delay_mins": 0,
                        "delay_reason": "On Time", "status": "Active", "seats": s_map
                    })
                    st.success("✅ Gaadi live ho gayi hai!")
                    st.rerun()
                else:
                    st.error("Saari details bharna zaroori hai.")

    with d2:
        if not active_trips:
            st.info("Koi active trip nahi hai.")
        else:
            d_map = {f"{t['driver']} - {t['vehicle']}": t for t in active_trips}
            st_trip = d_map[st.selectbox("Apni Gaadi Chunein:", list(d_map.keys()))]
            n_stop = st.selectbox("Abhi kahan pahunche hain?", st_trip["stops"], index=st_trip["current_stop_idx"])
            n_delay = st.radio("Delay:", [0, 10, 20, 30], format_func=lambda x: "On Time" if x == 0 else f"+{x} Min", horizontal=True)
            n_reason = st.text_input("Late hone ka karan", value=st_trip["delay_reason"])

            col_u, col_c = st.columns(2)
            if col_u.button("📡 Location Update Karein"):
                st_trip["current_stop_idx"] = st_trip["stops"].index(n_stop)
                st_trip["delay_mins"] = n_delay
                st_trip["delay_reason"] = "On Time" if n_delay == 0 else n_reason
                st.success("✅ Location update ho gayi!")
                st.rerun()
            if col_c.button("🚫 Poori Trip Cancel Karein"):
                st_trip["status"] = "Cancelled"
                st.error("Trip cancel kar di gayi hai.")
                st.rerun()
