import streamlit as st
import pandas as pd

from utils.slot_optimizer import get_available_slots, analyze_slot
from agent.decision_agent import make_decision
from agent.offer_generator import generate_offer
from agent.revenue_agent import optimize_slot_revenue
from agent.customer_agent import (
    create_customer_chat,
    ask_customer_agent
)

from analytics.demand_analysis import (
    get_overall_fill_rate,
    get_fill_rate_by_court,
    get_fill_rate_by_time
)

from analytics.revenue_analysis import (
    get_revenue_by_court,
    get_revenue_by_time,
    calculate_slot_economics
)
from utils.dynamic_pricing import get_slot_dynamic_price

from database.database import (
    save_agent_decision,
    get_agent_decisions,
    get_customer_available_slots,
    create_booking,
    apply_dynamic_price,
    get_dynamic_price_history,
    dispatch_notifications,
    get_notification_history,
    get_customer_bookings,
    cancel_booking
)


# -----------------------------------
# Page Configuration
# -----------------------------------

st.set_page_config(
    page_title="SmartSports",
    page_icon="🏟️",
    layout="wide"
)


# -----------------------------------
# Sidebar Navigation
# -----------------------------------

st.sidebar.title("🏟️ SmartSports")

dashboard = st.sidebar.radio(
    "Choose Dashboard",
    ["👤 Customer", "🛠️ Admin"]
)


# ==========================================================
# CUSTOMER DASHBOARD
# ==========================================================

if dashboard == "👤 Customer":

    st.title("🏟️ SmartSports")

    st.subheader("🎯 Find & Book Your Sports Slot")

    st.write(
        "Find available sports slots, compare prices, "
        "and book your preferred slot instantly."
    )

    st.divider()

    # -----------------------------------
    # Customer Information
    # -----------------------------------

    st.subheader("👤 Customer Details")

    customer_id = st.number_input(
        "Customer ID",
        min_value=1,
        value=1,
        step=1
    )

    st.divider()

    # -----------------------------------
    # Customer Navigation Tabs
    # -----------------------------------
    cust_tab1, cust_tab2, cust_tab3 = st.tabs([
        "📅 Find & Book Slots",
        "🤖 AI Booking Assistant",
        "🎟️ My Bookings & Manage"
    ])

    # ==========================================================
    # TAB 1: FIND & BOOK SLOTS
    # ==========================================================
    with cust_tab1:

        st.subheader("🔎 Find Available Slots")

        col1, col2 = st.columns(2)

        with col1:
            sport = st.selectbox(
                "🏅 Select Sport",
                ["All", "Football", "Badminton"]
            )

        with col2:
            selected_date = st.date_input(
                "📅 Select Date"
            )

        # Convert filters
        sport_filter = None if sport == "All" else sport
        date_filter = selected_date.strftime("%Y-%m-%d")

        # Get Available Customer Slots
        customer_slots = get_customer_available_slots(
            sport=sport_filter,
            slot_date=date_filter
        )

        st.divider()

        st.subheader("📅 Available Slots")

        if not customer_slots:
            st.info(
                "No available slots found for the selected sport and date."
            )
        else:
            st.success(
                f"{len(customer_slots)} available slot(s) found."
            )

            for slot in customer_slots:
                (
                    slot_id,
                    court_name,
                    sport_name,
                    slot_date,
                    start_time,
                    end_time,
                    base_price
                ) = slot

                col1, col2, col3, col4 = st.columns([2.5, 2.5, 1.5, 1.5])

                with col1:
                    st.write(f"### {sport_name}")
                    st.write(f"🏟️ {court_name}")

                with col2:
                    st.write(f"📅 **{slot_date}**")
                    st.write(f"⏰ {start_time} - {end_time}")

                with col3:
                    st.write("### Price")
                    st.write(f"**₹{base_price:,.0f}**")

                with col4:
                    st.write("### Action")
                    if st.button(
                        "🟢 Book Now",
                        key=f"book_{slot_id}",
                        type="primary"
                    ):
                        success, message = create_booking(
                            customer_id=customer_id,
                            slot_id=slot_id,
                            amount_paid=base_price
                        )
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

    # ==========================================================
    # TAB 2: AI CUSTOMER ASSISTANT
    # ==========================================================
    with cust_tab2:

        st.subheader("🤖 SmartSports AI Assistant")
        st.write(
            "Ask me to find or book sports slots using natural language."
        )

        # Create / Maintain Gemini Chat
        if (
            "customer_chat_agent" not in st.session_state
            or
            st.session_state.get("chat_customer_id") != customer_id
        ):
            st.session_state.customer_chat_agent = create_customer_chat(
                customer_id=customer_id
            )
            st.session_state.chat_customer_id = customer_id
            st.session_state.customer_chat = []

        # Display Previous Messages
        for message in st.session_state.customer_chat:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])

        # Chat Input
        user_message = st.chat_input(
            "Example: Find me a football slot tomorrow evening under ₹1000"
        )

        # Process Message
        if user_message:
            st.session_state.customer_chat.append(
                {"role": "user", "content": user_message}
            )

            with st.chat_message("user"):
                st.write(user_message)

            with st.chat_message("assistant"):
                with st.spinner("SmartSports AI is thinking..."):
                    try:
                        response = ask_customer_agent(
                            chat=st.session_state.customer_chat_agent,
                            message=user_message,
                            customer_id=customer_id
                        )
                        st.write(response)
                        st.session_state.customer_chat.append(
                            {"role": "assistant", "content": response}
                        )
                    except Exception as e:
                        st.error(f"AI Agent Error: {e}")
                        print("AI Agent Error:", repr(e))

    # ==========================================================
    # TAB 3: MY BOOKINGS & CANCELLATION
    # ==========================================================
    with cust_tab3:

        st.subheader("🎟️ My Booked Slots & History")
        st.caption("View your confirmed bookings and cancel or manage your reservations.")

        bookings, b_cols = get_customer_bookings(customer_id)

        if bookings:
            b_df = pd.DataFrame(bookings, columns=b_cols)
            total_b = len(b_df)
            active_b = sum(1 for b in bookings if b[8] == 'Confirmed')
            cancelled_b = sum(1 for b in bookings if b[8] == 'Cancelled')

            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.metric("Total Bookings", total_b)
            with m_col2:
                st.metric("🟢 Active Confirmed", active_b)
            with m_col3:
                st.metric("🔴 Cancelled", cancelled_b)

            st.divider()

            for b in bookings:
                (
                    b_id, s_id, court, sport_name,
                    s_date, s_time, e_time,
                    amount, status, booked_on
                ) = b

                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([2.5, 2.5, 2, 1.5])
                    with c1:
                        st.write(f"### {sport_name}")
                        st.write(f"🏟️ {court}")
                        st.caption(f"Booking ID: #{b_id} | Slot #{s_id}")

                    with c2:
                        st.write(f"📅 **{s_date}**")
                        st.write(f"⏰ {s_time} - {e_time}")
                        st.caption(f"Booked on: {booked_on}")

                    with c3:
                        st.write("### Price")
                        st.write(f"**₹{amount:,.0f}**")
                        if status == "Confirmed":
                            st.success("🟢 Confirmed")
                        else:
                            st.error("🔴 Cancelled")

                    with c4:
                        st.write("### Action")
                        if status == "Confirmed":
                            if st.button(
                                "❌ Cancel",
                                key=f"cancel_{b_id}",
                                type="secondary",
                                use_container_width=True
                            ):
                                ok, msg = cancel_booking(b_id)
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        else:
                            st.caption("Cancelled")
        else:
            st.info("You have no bookings recorded yet. Select 'Find & Book Slots' to reserve a court!")
  

# ==========================================================
# ADMIN DASHBOARD
# ==========================================================

if dashboard == "🛠️ Admin":

    # -----------------------------------
    # Header
    # -----------------------------------

    st.title("🏟️ SmartSports")

    st.subheader(
        "AI-Powered Sports Facility Revenue Optimization"
    )

    st.write(
        "SmartSports analyzes vacant sports slots, evaluates demand, "
        "identifies likely customers, and recommends the best action "
        "to improve slot utilization and revenue."
    )

    # -----------------------------------
    # Get Available Slots
    # -----------------------------------

    available_slots = get_available_slots()

    # -----------------------------------
    # Dashboard Metrics
    # -----------------------------------

    low_demand = 0

    for _, slot in available_slots.iterrows():

        analysis = analyze_slot(slot)

        if analysis["demand_level"] == "Low":

            low_demand += 1

    potential_revenue = available_slots["base_price"].sum()

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Available Slots",
            len(available_slots)
        )

    with col2:

        st.metric(
            "Low Demand Slots",
            low_demand
        )

    with col3:

        st.metric(
            "Potential Revenue",
            f"₹{potential_revenue:,.0f}"
        )

    st.divider()

    # -----------------------------------
    # Available Slots
    # -----------------------------------

    st.header("📅 Available Slots")

    if available_slots.empty:

        st.info(
            "No future vacant slots available."
        )

    else:

        display_data = available_slots[
            [
                "slot_id",
                "court_name",
                "sport",
                "slot_date",
                "start_time",
                "end_time",
                "base_price"
            ]
        ].copy()

        display_data.columns = [
            "Slot ID",
            "Court",
            "Sport",
            "Date",
            "Start Time",
            "End Time",
            "Price"
        ]

        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True
        )

    # -----------------------------------
    # AI Slot Analysis
    # -----------------------------------

    st.divider()

    # -----------------------------------
    # Unified Revenue Optimization Agent
    # -----------------------------------

    st.divider()

    st.header("⚡ Unified Revenue Optimization Agent")

    st.write(
        "Combines real-time demand analysis, dynamic pricing, profit economics, "
        "and behavioral customer segmentation into an actionable revenue strategy."
    )

    if not available_slots.empty:

        slot_options_map = {
            f"Slot #{row['slot_id']} | {row['court_name']} ({row['sport']}) | {row['slot_date']} {row['start_time']}-{row['end_time']} (Base: ₹{row['base_price']:,.0f})": row['slot_id']
            for _, row in available_slots.iterrows()
        }

        selected_label = st.selectbox(
            "Select a vacant slot to analyze:",
            list(slot_options_map.keys()),
            key="rev_agent_slot_select"
        )

        chosen_slot_id = slot_options_map[selected_label]
        selected_slot = available_slots[
            available_slots["slot_id"] == chosen_slot_id
        ].iloc[0]

        if st.button(
            "🔍 Run Revenue Agent",
            type="primary",
            key="btn_run_revenue_agent"
        ):
            st.session_state.active_revenue_analysis = optimize_slot_revenue(selected_slot)

        if "active_revenue_analysis" in st.session_state and st.session_state.active_revenue_analysis.get("slot_id") == chosen_slot_id:
            rev_res = st.session_state.active_revenue_analysis

            # -----------------------------------
            # Slot & Demand Snapshot
            # -----------------------------------
            st.subheader("📍 Slot & Demand Intelligence")

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.write("**🏟️ Court & Sport**")
                st.write(f"{rev_res['court_name']} ({rev_res['sport']})")

            with c2:
                st.write("**📅 Date & Time**")
                st.write(f"{rev_res['slot_date']} ({rev_res['start_time']} - {rev_res['end_time']})")

            with c3:
                st.metric("Historical Fill Rate", f"{rev_res['historical_fill_rate']:.1f}%")

            with c4:
                demand_badge = "🔥 HIGH" if rev_res['demand_level'] == "HIGH" else ("📊 MEDIUM" if rev_res['demand_level'] == "MEDIUM" else "📉 LOW")
                st.metric("Demand Level", demand_badge)

            # -----------------------------------
            # Dynamic Pricing & Profit Impact
            # -----------------------------------
            st.subheader("💰 Dynamic Pricing & Profit Economics")

            p1, p2, p3, p4 = st.columns(4)
            with p1:
                st.metric("Base Price", f"₹{rev_res['base_price']:,.0f}")

            with p2:
                price_diff = rev_res['suggested_price'] - rev_res['base_price']
                st.metric(
                    "Dynamic Price",
                    f"₹{rev_res['suggested_price']:,.0f}",
                    delta=f"{price_diff:+,.0f} ({rev_res['adjustment_percentage']:+.0f}%)"
                )

            with p3:
                st.metric("Estimated Profit", f"₹{rev_res['estimated_profit']:,.0f}")

            with p4:
                st.metric("Profit Margin", f"{rev_res['profit_margin']:.1f}%")

            # -----------------------------------
            # Strategic Decision & Reasoning
            # -----------------------------------
            st.subheader("🧠 Strategic Revenue Decision")
            st.success(f"🎯 Recommended Strategy: **{rev_res['action']}**")
            st.info(f"💡 **Agent Reasoning**: {rev_res['reasoning']}")

            # -----------------------------------
            # Target Customers & Offer Message
            # -----------------------------------
            col_cust, col_msg = st.columns([1, 1])

            with col_cust:
                st.subheader("👥 Prioritized Target Customers")
                target_custs = rev_res.get("target_customers", [])
                if target_custs:
                    for idx, c in enumerate(target_custs, start=1):
                        st.markdown(
                            f"**{idx}. {c['name']}** ({c['customer_type']})  \n"
                            f"📧 `{c['email']}` | Bookings: **{c['booking_frequency']}** | Affinity Score: **{c['score']:.0f}**"
                        )
                else:
                    st.write("No matching customer profiles identified.")

            with col_msg:
                st.subheader("📢 Generated Outreach Message")
                st.code(rev_res["offer_message"], language="text")

            st.divider()

            # -----------------------------------
            # One-Click Strategy Execution
            # -----------------------------------
            st.subheader("🚀 One-Click Strategy Execution")
            st.caption(
                "Executing will: (1) Apply the dynamic price in the database, "
                "(2) Log the decision audit trail, and (3) Stage personalized notifications for target customers."
            )

            if st.button(
                "⚡ Execute Revenue Strategy",
                type="primary",
                key=f"exec_strat_{rev_res['slot_id']}",
                use_container_width=True
            ):
                # 1. Apply dynamic price
                apply_dynamic_price(
                    slot_id=rev_res["slot_id"],
                    approved_price=rev_res["suggested_price"],
                    base_price=rev_res["base_price"],
                    suggested_price=rev_res["suggested_price"],
                    adjustment_percentage=rev_res["adjustment_percentage"],
                    demand=rev_res["demand_level"],
                    status="Approved"
                )

                # 2. Save decision
                save_agent_decision(
                    slot_id=rev_res["slot_id"],
                    decision=rev_res["action"],
                    discount_percentage=abs(rev_res["adjustment_percentage"]),
                    reason=rev_res["reasoning"],
                    offer_message=rev_res["offer_message"]
                )

                # 3. Dispatch notifications
                notif_count = dispatch_notifications(
                    slot_id=rev_res["slot_id"],
                    target_customers=rev_res["target_customers"],
                    message=rev_res["offer_message"]
                )

                st.success(
                    f"🎉 Revenue Strategy Executed! Price updated to ₹{rev_res['suggested_price']:,.0f} "
                    f"and {notif_count} personalized notifications dispatched!"
                )
                del st.session_state.active_revenue_analysis
                st.rerun()
        # -----------------------------------
    # Dynamic Pricing Dashboard
    # -----------------------------------

    st.divider()

    st.header(
        "💰 Dynamic Pricing"
    )

    st.write(
        "Evaluate real-time demand, adjust prices dynamically to maximize facility revenue, "
        "and approve price modifications before they go live."
    )

    if not available_slots.empty:

        all_pricing_data = []

        for _, slot in available_slots.iterrows():

            pricing = get_slot_dynamic_price(
                slot["slot_id"]
            )

            if pricing:
                all_pricing_data.append(pricing)

        if all_pricing_data:

            # -----------------------------------
            # Filters Row
            # -----------------------------------
            st.subheader("🔎 Dynamic Pricing Filters")

            filter_col1, filter_col2, filter_col3 = st.columns(3)

            with filter_col1:
                sports_list = ["All"] + sorted(
                    list({p["sport"] for p in all_pricing_data})
                )
                selected_sport_filter = st.selectbox(
                    "🏅 Filter by Sport",
                    sports_list,
                    key="dyn_sport_filter"
                )

            with filter_col2:
                selected_demand_filter = st.selectbox(
                    "📈 Filter by Demand",
                    ["All", "HIGH", "MEDIUM", "LOW"],
                    key="dyn_demand_filter"
                )

            with filter_col3:
                dates_list = ["All Dates"] + sorted(
                    list({p["date"] for p in all_pricing_data})
                )
                selected_date_filter = st.selectbox(
                    "📅 Filter by Date",
                    dates_list,
                    key="dyn_date_filter"
                )

            # Apply filters
            filtered_pricing = [
                p for p in all_pricing_data
                if (selected_sport_filter == "All" or p["sport"] == selected_sport_filter)
                and (selected_demand_filter == "All" or p["demand"] == selected_demand_filter)
                and (selected_date_filter == "All Dates" or p["date"] == selected_date_filter)
            ]

            # -----------------------------------
            # Pricing Summary (Filtered)
            # -----------------------------------
            high_demand = sum(1 for p in filtered_pricing if p["demand"] == "HIGH")
            medium_demand = sum(1 for p in filtered_pricing if p["demand"] == "MEDIUM")
            low_demand = sum(1 for p in filtered_pricing if p["demand"] == "LOW")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("🎯 Filtered Slots", len(filtered_pricing))

            with col2:
                st.metric("🔥 High Demand (+10% to +15%)", high_demand)

            with col3:
                st.metric("📊 Medium Demand (Base)", medium_demand)

            with col4:
                st.metric("📉 Low Demand (-10% to -15%)", low_demand)

            st.divider()

            # -----------------------------------
            # Human-in-the-Loop Price Approval
            # -----------------------------------
            st.subheader("🎯 Review & Approve Dynamic Price")
            st.caption(
                "Select a slot below to review its pricing analysis and approve price updates in real time. "
                "Approved prices immediately update the booking price in the database."
            )

            if filtered_pricing:
                slot_options = {
                    (
                        f"Slot #{p['slot_id']} | {p['court_name']} ({p['sport']}) | "
                        f"{p['date']} {p['start_time']}-{p['end_time']} | "
                        f"Base: ₹{p['base_price']:,.0f} ➔ Suggested: ₹{p['suggested_price']:,.0f} ({p['demand']})"
                    ): p
                    for p in filtered_pricing
                }

                chosen_label = st.selectbox(
                    "Select slot to review / update:",
                    list(slot_options.keys()),
                    key="select_slot_approval"
                )

                selected_p = slot_options[chosen_label]

                # Review Card
                with st.container(border=True):
                    rev_col1, rev_col2, rev_col3, rev_col4 = st.columns(4)

                    with rev_col1:
                        st.write("**🏟️ Court & Sport**")
                        st.write(f"{selected_p['court_name']} ({selected_p['sport']})")

                    with rev_col2:
                        st.write("**📅 Date & Time**")
                        st.write(f"{selected_p['date']} ({selected_p['start_time']} - {selected_p['end_time']})")

                    with rev_col3:
                        st.write("**📊 Demand & Fill Rate**")
                        demand_emoji = "🔥" if selected_p['demand'] == "HIGH" else ("📊" if selected_p['demand'] == "MEDIUM" else "📉")
                        st.write(f"{demand_emoji} {selected_p['demand']} ({selected_p['historical_fill_rate']:.1%})")

                    with rev_col4:
                        st.write("**⏳ Days to Slot**")
                        st.write(f"{selected_p['days_until_slot']} day(s)")

                    st.markdown("---")

                    p_col1, p_col2, p_col3 = st.columns(3)

                    with p_col1:
                        st.metric("Base Price", f"₹{selected_p['base_price']:,.0f}")

                    with p_col2:
                        st.metric(
                            "Adjustment",
                            f"{selected_p['adjustment_percentage']:+.0f}%"
                        )

                    with p_col3:
                        diff = selected_p["suggested_price"] - selected_p["base_price"]
                        st.metric(
                            "Suggested Price",
                            f"₹{selected_p['suggested_price']:,.0f}",
                            delta=f"{diff:+,.0f}"
                        )

                    # Action Buttons
                    btn_col1, btn_col2, btn_col3 = st.columns([1.5, 1.2, 1.5])

                    with btn_col1:
                        if st.button(
                            f"🟢 Approve Suggested (₹{selected_p['suggested_price']:,.0f})",
                            key=f"approve_{selected_p['slot_id']}",
                            type="primary",
                            use_container_width=True
                        ):
                            success, msg = apply_dynamic_price(
                                slot_id=selected_p["slot_id"],
                                approved_price=selected_p["suggested_price"],
                                base_price=selected_p["base_price"],
                                suggested_price=selected_p["suggested_price"],
                                adjustment_percentage=selected_p["adjustment_percentage"],
                                demand=selected_p["demand"],
                                status="Approved"
                            )
                            if success:
                                st.success(msg)
                                st.rerun()

                    with btn_col2:
                        if st.button(
                            f"⚪ Keep Base Price",
                            key=f"keep_{selected_p['slot_id']}",
                            use_container_width=True
                        ):
                            success, msg = apply_dynamic_price(
                                slot_id=selected_p["slot_id"],
                                approved_price=selected_p["base_price"],
                                base_price=selected_p["base_price"],
                                suggested_price=selected_p["suggested_price"],
                                adjustment_percentage=0,
                                demand=selected_p["demand"],
                                status="Kept Base"
                            )
                            st.info(f"Slot #{selected_p['slot_id']} retained at base price ₹{selected_p['base_price']:,.0f}.")
                            st.rerun()

                    with btn_col3:
                        with st.popover("✏️ Apply Custom Price", use_container_width=True):
                            custom_val = st.number_input(
                                "Enter Custom Price (₹)",
                                min_value=100.0,
                                max_value=10000.0,
                                value=float(selected_p["suggested_price"]),
                                step=50.0,
                                key=f"custom_input_{selected_p['slot_id']}"
                            )
                            if st.button(
                                "Confirm Custom Price",
                                key=f"btn_custom_{selected_p['slot_id']}",
                                type="primary"
                            ):
                                custom_adj = round(
                                    ((custom_val - selected_p["base_price"]) / selected_p["base_price"]) * 100,
                                    1
                                )
                                success, msg = apply_dynamic_price(
                                    slot_id=selected_p["slot_id"],
                                    approved_price=custom_val,
                                    base_price=selected_p["base_price"],
                                    suggested_price=selected_p["suggested_price"],
                                    adjustment_percentage=custom_adj,
                                    demand=selected_p["demand"],
                                    status="Modified"
                                )
                                if success:
                                    st.success(msg)
                                    st.rerun()
            else:
                st.info("No slots match the selected filters for review.")

            st.divider()

            # -----------------------------------
            # Pricing Recommendations Table
            # -----------------------------------
            st.subheader(f"💵 Pricing Recommendations ({len(filtered_pricing)} slots)")

            if filtered_pricing:
                table_rows = []
                for p in filtered_pricing:
                    table_rows.append(
                        {
                            "Slot ID": p["slot_id"],
                            "Court": p["court_name"],
                            "Sport": p["sport"],
                            "Date": p["date"],
                            "Time": f"{p['start_time']} - {p['end_time']}",
                            "Demand": p["demand"],
                            "Fill Rate": f"{p['historical_fill_rate']:.1%}",
                            "Base Price": f"₹{p['base_price']:,.0f}",
                            "Adjustment": f"{p['adjustment_percentage']:+.0f}%",
                            "Suggested Price": f"₹{p['suggested_price']:,.0f}"
                        }
                    )

                pricing_df = pd.DataFrame(table_rows)

                st.dataframe(
                    pricing_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No slots match the active filters.")

        else:
            st.info("No pricing recommendations available.")

    else:
        st.info("No future vacant slots available for pricing analysis.")

    # -----------------------------------
    # Dynamic Pricing History / Audit Log
    # -----------------------------------
    st.divider()

    st.subheader("📝 Approved Dynamic Pricing History")
    st.caption("Audit log of approved, custom-modified, or dismissed pricing actions.")

    history_records, history_cols = get_dynamic_price_history()

    if history_records:
        history_df = pd.DataFrame(history_records, columns=history_cols)

        display_history_df = history_df[
            [
                "price_id",
                "slot_id",
                "court_name",
                "sport",
                "slot_date",
                "start_time",
                "end_time",
                "base_price",
                "suggested_price",
                "approved_price",
                "adjustment_percentage",
                "demand",
                "status",
                "created_at"
            ]
        ].copy()

        display_history_df.columns = [
            "Price ID",
            "Slot ID",
            "Court",
            "Sport",
            "Date",
            "Start Time",
            "End Time",
            "Base Price",
            "Suggested Price",
            "Approved Price",
            "Adjustment %",
            "Demand",
            "Status",
            "Recorded At"
        ]

        # Format price columns with Rupee symbol
        display_history_df["Base Price"] = display_history_df["Base Price"].apply(lambda x: f"₹{x:,.0f}")
        display_history_df["Suggested Price"] = display_history_df["Suggested Price"].apply(lambda x: f"₹{x:,.0f}")
        display_history_df["Approved Price"] = display_history_df["Approved Price"].apply(lambda x: f"₹{x:,.0f}")
        display_history_df["Adjustment %"] = display_history_df["Adjustment %"].apply(lambda x: f"{x:+.0f}%")

        st.dataframe(
            display_history_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No dynamic pricing actions have been approved yet.")

    # -----------------------------------
    # Analytics Dashboard
    # -----------------------------------

    st.divider()

    st.header(
        "📈 Facility Analytics"
    )

    st.write(
        "Historical booking and revenue analytics used to "
        "identify demand patterns and optimization opportunities."
    )

    # -----------------------------------
    # Analytics Metrics
    # -----------------------------------

    overall_fill_rate = (
        get_overall_fill_rate()
    )

    revenue_by_court = (
        get_revenue_by_court()
    )

    total_historical_revenue = (
        revenue_by_court["revenue"].sum()
    )

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Historical Fill Rate",
            f"{overall_fill_rate}%"
        )

    with col2:

        st.metric(
            "Historical Revenue",
            f"₹{total_historical_revenue:,.0f}"
        )

    # -----------------------------------
    # Fill Rate By Time
    # -----------------------------------

    st.subheader(
        "⏰ Demand by Time Slot"
    )

    fill_rate_time = (
        get_fill_rate_by_time()
    )

    st.bar_chart(
        fill_rate_time.set_index(
            "start_time"
        )["fill_rate"],
        use_container_width=True
    )

    # -----------------------------------
    # Fill Rate By Court
    # -----------------------------------

    st.subheader(
        "🏟️ Court Performance"
    )

    fill_rate_court = (
        get_fill_rate_by_court()
    )

    st.bar_chart(
        fill_rate_court.set_index(
            "court_name"
        )["fill_rate"],
        use_container_width=True
    )

    # -----------------------------------
    # Revenue By Court
    # -----------------------------------

    st.subheader(
        "💰 Revenue by Court"
    )

    st.bar_chart(
        revenue_by_court.set_index(
            "court_name"
        )["revenue"],
        use_container_width=True
    )

    # -----------------------------------
    # Revenue By Time
    # -----------------------------------

    st.subheader(
        "💵 Revenue by Time Slot"
    )

    revenue_time = (
        get_revenue_by_time()
    )

    st.bar_chart(
        revenue_time.set_index(
            "start_time"
        )["revenue"],
        use_container_width=True
    )

    # -----------------------------------
    # Agent Decision History
    # -----------------------------------

    st.divider()

    st.header(
        "📝 Agent Decision History"
    )

    decisions, decision_columns = (
        get_agent_decisions()
    )

    if decisions:

        decision_df = pd.DataFrame(
            decisions,
            columns=decision_columns
        )

        display_history = decision_df[
            [
                "decision_id",
                "slot_id",
                "court_name",
                "sport",
                "slot_date",
                "start_time",
                "end_time",
                "decision",
                "discount_percentage",
                "created_at"
            ]
        ].copy()

        display_history.columns = [
            "Decision ID",
            "Slot ID",
            "Court",
            "Sport",
            "Date",
            "Start Time",
            "End Time",
            "Decision",
            "Discount %",
            "Created At"
        ]

        st.dataframe(
            display_history,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No agent decisions have been recorded yet."
        )

    # -----------------------------------
    # Outbound Notification Log
    # -----------------------------------

    st.divider()

    st.header(
        "📢 Outbound Notification Dispatch Log"
    )

    st.write(
        "Audit log of personalized promotional notifications generated and dispatched "
        "by the Unified Revenue Optimization Agent."
    )

    notif_rows, notif_cols = get_notification_history()

    if notif_rows:

        notif_df = pd.DataFrame(
            notif_rows,
            columns=notif_cols
        )

        display_notifs = notif_df[
            [
                "notification_id",
                "slot_id",
                "court_name",
                "sport",
                "slot_date",
                "start_time",
                "end_time",
                "recipient_name",
                "channel",
                "message",
                "sent_at"
            ]
        ].copy()

        display_notifs.columns = [
            "Notif ID",
            "Slot ID",
            "Court",
            "Sport",
            "Date",
            "Start Time",
            "End Time",
            "Recipient",
            "Channel",
            "Dispatched Message",
            "Sent At"
        ]

        st.dataframe(
            display_notifs,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No marketing notifications have been dispatched yet. "
            "Run the Revenue Agent above and click 'Execute Revenue Strategy' to dispatch offers!"
        )