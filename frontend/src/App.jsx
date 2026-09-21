import React, { useState, useEffect } from "react";
import {
  LayoutDashboard,
  Calendar,
  MessageSquare,
  DollarSign,
  Activity,
  User,
  Search,
  Bell,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Zap,
  Users,
  ExternalLink,
  ShieldCheck,
  Send,
  CreditCard,
  Trophy,
  ArrowLeft,
  ArrowRight,
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  // Selected Portal: null (Landing / Role Selection) | 'customer' | 'admin'
  const [activePortal, setActivePortal] = useState(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const roleParam = params.get("role");
      if (roleParam === "customer" || roleParam === "admin") {
        return roleParam;
      }
      const saved = sessionStorage.getItem("smartsports_role");
      if (saved === "customer" || saved === "admin") {
        return saved;
      }
    } catch {
      // Fallback if sessionStorage is restricted
    }
    return null;
  });

  const selectRole = (role) => {
    setActivePortal(role);
    try {
      if (role) {
        sessionStorage.setItem("smartsports_role", role);
      } else {
        sessionStorage.removeItem("smartsports_role");
        if (window.location.search) {
          window.history.replaceState({}, document.title, window.location.pathname);
        }
      }
    } catch {
      // Fallback
    }
  };

  const [customerId, setCustomerId] = useState(1);
  const [backendOnline, setBackendOnline] = useState(true);

  // Customer Tabs: 'dashboard' | 'bookings' | 'chat'
  const [customerTab, setCustomerTab] = useState("dashboard");
  const [sportFilter, setSportFilter] = useState("All");
  const [selectedDate, setSelectedDate] = useState("2026-09-21");
  const [timeFilter, setTimeFilter] = useState("All"); // 'All' | 'morning' | 'afternoon' | 'evening'
  const [slots, setSlots] = useState([]);
  const [customerBookings, setCustomerBookings] = useState([]);
  const [loadingSlots, setLoadingSlots] = useState(false);

  // Assistant Chat State
  const [chatMessages, setChatMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello. I am the SmartSports booking assistant. How can I help you with court availability or reservations today?",
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  // Admin Tabs: 'revenue' | 'pricing' | 'analytics' | 'notifications'
  const [adminTab, setAdminTab] = useState("revenue");
  const [adminSlots, setAdminSlots] = useState([]);
  const [selectedSlotId, setSelectedSlotId] = useState(null);
  const [revenueAnalysis, setRevenueAnalysis] = useState(null);
  const [executingStrategy, setExecutingStrategy] = useState(false);

  // Dynamic Pricing State
  const [pricingRecommendations, setPricingRecommendations] = useState([]);
  const [pricingHistory, setPricingHistory] = useState([]);
  const [pricingDemandFilter, setPricingDemandFilter] = useState("All");
  const [pricingSportFilter, setPricingSportFilter] = useState("All");
  const [selectedPricingSlot, setSelectedPricingSlot] = useState(null);
  const [customPriceInput, setCustomPriceInput] = useState("");

  // Analytics & Notifications State
  const [analytics, setAnalytics] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [notificationBanner, setNotificationBanner] = useState(null);

  const showBanner = (msg, type = "success") => {
    setNotificationBanner({ msg, type });
    setTimeout(() => setNotificationBanner(null), 4000);
  };

  // ------------------------------------------------------------------
  // Data Fetching & Sync
  // ------------------------------------------------------------------

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/health`);
      setBackendOnline(res.ok);
    } catch {
      setBackendOnline(false);
    }
  };

  const fetchCustomerSlots = async () => {
    setLoadingSlots(true);
    try {
      const params = new URLSearchParams();
      if (sportFilter !== "All") params.append("sport", sportFilter);
      if (selectedDate) params.append("date", selectedDate);
      if (timeFilter !== "All") params.append("preferred_time", timeFilter);

      const res = await fetch(`${API_BASE}/api/slots?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setSlots(data);
      }
    } catch (e) {
      console.error("Error loading slots:", e);
    } finally {
      setLoadingSlots(false);
    }
  };

  const fetchCustomerBookings = async () => {
    try {
      const res = await fetch(
        `${API_BASE}/api/customers/${customerId}/bookings`
      );
      if (res.ok) {
        const data = await res.json();
        setCustomerBookings(data);
      }
    } catch (e) {
      console.error("Error loading bookings:", e);
    }
  };

  const fetchAdminData = async () => {
    try {
      const [slotsRes, pricingRes, analyticsRes, notifRes, historyRes] =
        await Promise.all([
          fetch(`${API_BASE}/api/admin/slots`),
          fetch(`${API_BASE}/api/pricing/recommendations`),
          fetch(`${API_BASE}/api/analytics/summary`),
          fetch(`${API_BASE}/api/notifications/history`),
          fetch(`${API_BASE}/api/pricing/history`),
        ]);

      if (slotsRes.ok) {
        const slotsData = await slotsRes.json();
        setAdminSlots(slotsData);
        if (slotsData.length > 0 && !selectedSlotId) {
          setSelectedSlotId(slotsData[0].slot_id);
        }
      }
      if (pricingRes.ok) setPricingRecommendations(await pricingRes.json());
      if (analyticsRes.ok) setAnalytics(await analyticsRes.json());
      if (notifRes.ok) setNotifications(await notifRes.json());
      if (historyRes.ok) setPricingHistory(await historyRes.json());
    } catch (e) {
      console.error("Admin data fetch error:", e);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  useEffect(() => {
    if (activePortal === "admin") {
      fetchAdminData();
    } else if (activePortal === "customer") {
      fetchCustomerSlots();
      fetchCustomerBookings();
    }
  }, [activePortal]);

  useEffect(() => {
    if (activePortal === "customer") {
      fetchCustomerSlots();
      fetchCustomerBookings();
    }
  }, [customerId, sportFilter, selectedDate, timeFilter]);

  // ------------------------------------------------------------------
  // Actions
  // ------------------------------------------------------------------

  const handleBookSlot = async (slotId, price) => {
    try {
      const res = await fetch(`${API_BASE}/api/bookings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: customerId,
          slot_id: slotId,
          amount_paid: price,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        showBanner(data.message, "success");
        fetchCustomerSlots();
        fetchCustomerBookings();
        fetchAdminData();
      } else {
        showBanner(data.detail || "Booking failed", "error");
      }
    } catch (e) {
      showBanner("Failed to connect to booking service", "error");
    }
  };

  const handleCancelBooking = async (bookingId) => {
    try {
      const res = await fetch(`${API_BASE}/api/bookings/${bookingId}`, {
        method: "DELETE",
      });
      const data = await res.json();
      if (res.ok) {
        showBanner(data.message, "info");
        fetchCustomerBookings();
        fetchCustomerSlots();
        fetchAdminData();
      } else {
        showBanner(data.detail || "Cancellation failed", "error");
      }
    } catch (e) {
      showBanner("Error canceling booking", "error");
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || chatLoading) return;

    const userText = inputMessage.trim();
    setInputMessage("");
    setChatMessages((prev) => [...prev, { role: "user", content: userText }]);
    setChatLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer_id: customerId,
          message: userText,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        const replyContent = data.response || data.reply || data.message || "I couldn't find any courts matching your query.";
        setChatMessages((prev) => [
          ...prev,
          { role: "assistant", content: replyContent },
        ]);
      } else {
        setChatMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "The assistant service is currently unavailable. Please try again.",
          },
        ]);
      }
    } catch {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Unable to connect to the assistant server.",
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleRunRevenueAgent = async () => {
    if (!selectedSlotId) return;
    try {
      const res = await fetch(
        `${API_BASE}/api/revenue/optimize/${selectedSlotId}`
      );
      if (res.ok) {
        const data = await res.json();
        setRevenueAnalysis(data);
        showBanner("Recommendation generated", "success");
      }
    } catch (e) {
      showBanner("Error analyzing slot", "error");
    }
  };

  const handleExecuteRevenueStrategy = async () => {
    if (!revenueAnalysis) return;
    setExecutingStrategy(true);
    try {
      const res = await fetch(`${API_BASE}/api/revenue/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slot_id: revenueAnalysis.slot_id,
          suggested_price: revenueAnalysis.suggested_price,
          base_price: revenueAnalysis.base_price,
          adjustment_percentage: revenueAnalysis.adjustment_percentage,
          demand_level: revenueAnalysis.demand_level,
          action: revenueAnalysis.action,
          reasoning: revenueAnalysis.reasoning,
          offer_message: revenueAnalysis.offer_message,
          target_customers: revenueAnalysis.target_customers,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        showBanner("Rate updated and notifications dispatched", "success");
        fetchAdminData();
      } else {
        showBanner(data.detail || "Update failed", "error");
      }
    } catch (e) {
      showBanner("Failed to apply rate recommendation", "error");
    } finally {
      setExecutingStrategy(false);
    }
  };

  const handleApprovePrice = async (slotId, approvedPrice, status) => {
    try {
      const adj = Math.round(
        ((approvedPrice - selectedPricingSlot.base_price) /
          selectedPricingSlot.base_price) *
          100
      );
      const res = await fetch(`${API_BASE}/api/pricing/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slot_id: slotId,
          approved_price: approvedPrice,
          base_price: selectedPricingSlot.base_price,
          suggested_price: selectedPricingSlot.suggested_price,
          adjustment_percentage: adj,
          demand: selectedPricingSlot.demand,
          status: status,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        showBanner(data.message, "success");
        fetchAdminData();
      } else {
        showBanner("Approval failed", "error");
      }
    } catch (e) {
      showBanner("Error approving rate", "error");
    }
  };

  const filteredPricing = pricingRecommendations.filter((p) => {
    const matchSport =
      pricingSportFilter === "All" || p.sport === pricingSportFilter;
    const matchDemand =
      pricingDemandFilter === "All" || p.demand === pricingDemandFilter;
    return matchSport && matchDemand;
  });

  return (
    <div className="min-h-screen bg-[#f7f9fb] text-slate-800 flex flex-col font-sans">
      {/* Toast Notification Banner */}
      {notificationBanner && (
        <div
          className={`fixed top-5 right-5 z-50 px-4 py-3 rounded-xl shadow-lg border flex items-center space-x-2.5 text-xs font-semibold bg-white transition-all ${
            notificationBanner.type === "success"
              ? "border-emerald-300 text-emerald-800"
              : notificationBanner.type === "error"
              ? "border-rose-300 text-rose-800"
              : "border-slate-300 text-slate-800"
          }`}
        >
          {notificationBanner.type === "success" && (
            <CheckCircle className="w-4 h-4 text-emerald-600" />
          )}
          {notificationBanner.type === "error" && (
            <XCircle className="w-4 h-4 text-rose-600" />
          )}
          {notificationBanner.type === "info" && (
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          )}
          <span>{notificationBanner.msg}</span>
        </div>
      )}

      {/* 1. TOP NAVBAR */}
      <header className="bg-white border-b border-slate-100 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Brand Logo */}
          <div className="flex items-center space-x-6">
            <div
              className="flex items-center space-x-2.5 cursor-pointer"
              onClick={() => selectRole(null)}
              title="Return to Home"
            >
              <div className="w-9 h-9 rounded-xl bg-emerald-50 text-[#00875a] flex items-center justify-center font-bold shadow-2xs border border-emerald-100/60">
                <svg
                  className="w-5 h-5 text-[#00875a]"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="m14 10-2-2-4 4 2 2" />
                  <path d="M10.5 7.5 13 5a3 3 0 1 1 4.2 4.2l-2.5 2.5" />
                  <path d="m7.5 10.5-2.5 2.5a3 3 0 1 0 4.2 4.2l2.5-2.5" />
                  <path d="m15.5 15.5 4 4" />
                </svg>
              </div>
              <div className="leading-tight">
                <span className="text-lg font-black tracking-tight text-slate-900">
                  Smart<span className="text-[#00875a]">Sports</span>
                </span>
                <span className="block text-[9px] font-bold uppercase tracking-widest text-slate-400">
                  Facility Management
                </span>
              </div>
            </div>

            {/* Quick Search (Only active when inside a dashboard) */}
            {activePortal && (
              <div className="hidden md:flex items-center relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 pointer-events-none" />
                <input
                  type="text"
                  placeholder={
                    activePortal === "customer"
                      ? "Search courts or bookings..."
                      : "Search slots or pricing..."
                  }
                  className="bg-slate-50 border border-slate-200/80 rounded-full pl-8 pr-4 py-1.5 text-xs text-slate-700 w-56 focus:outline-none focus:border-emerald-500 focus:bg-white transition-all placeholder:text-slate-400"
                />
              </div>
            )}
          </div>

          {/* Right Header Controls */}
          <div className="flex items-center space-x-3 sm:space-x-4">
            {/* If inside Customer Portal: Show Role Badge & Switch Role Button */}
            {activePortal === "customer" && (
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-1.5 px-3 py-1 bg-emerald-50 text-[#00875a] border border-emerald-100 rounded-lg text-xs font-bold">
                  <User className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Customer Portal</span>
                </div>
                <button
                  onClick={() => selectRole(null)}
                  className="flex items-center space-x-1 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-600 hover:text-slate-900 border border-slate-200 rounded-lg text-xs font-semibold transition-all shadow-2xs"
                  title="Return to role selection"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Switch Role</span>
                </button>
              </div>
            )}

            {/* If inside Admin Console: Show Role Badge & Switch Role Button */}
            {activePortal === "admin" && (
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-1.5 px-3 py-1 bg-slate-900 text-white rounded-lg text-xs font-bold shadow-xs">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Admin Console</span>
                </div>
                <button
                  onClick={() => selectRole(null)}
                  className="flex items-center space-x-1 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-600 hover:text-slate-900 border border-slate-200 rounded-lg text-xs font-semibold transition-all shadow-2xs"
                  title="Return to role selection"
                >
                  <ArrowLeft className="w-3.5 h-3.5" />
                  <span>Switch Role</span>
                </button>
              </div>
            )}

            {/* Customer Switcher (visible in Customer Portal) */}
            {activePortal === "customer" && (
              <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
                <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center font-bold text-xs shadow-sm">
                  C{customerId}
                </div>
                <div className="hidden sm:block text-left text-xs">
                  <span className="font-bold text-slate-900 block leading-none">
                    Customer #{customerId}
                  </span>
                  <select
                    value={customerId}
                    onChange={(e) => setCustomerId(parseInt(e.target.value) || 1)}
                    className="text-[11px] text-slate-500 bg-transparent border-0 p-0 focus:outline-none cursor-pointer"
                  >
                    {[...Array(30)].map((_, i) => (
                      <option key={i + 1} value={i + 1}>
                        User #{i + 1}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {/* API Documentation Link */}
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="hidden sm:flex items-center space-x-1 text-xs font-semibold text-slate-500 hover:text-[#00875a] transition-colors"
            >
              <span>API Docs</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </header>

      {!activePortal ? (
        /* ========================================================= */
        /* LANDING / ROLE SELECTION SCREEN */
        /* ========================================================= */
        <div className="flex-1 flex flex-col">
          {/* Landing Hero */}
          <section className="bg-gradient-to-r from-[#14192b] via-[#1c1d3b] to-[#121524] text-white pt-16 pb-28 relative overflow-hidden text-center">
            {/* Ambient glowing elements */}
            <div className="absolute top-6 left-12 w-4 h-4 rounded-full bg-teal-400/40 blur-sm pointer-events-none" />
            <div className="absolute top-10 right-20 w-6 h-6 rounded-full bg-teal-300/30 blur-sm pointer-events-none" />
            <div className="absolute -bottom-10 right-1/4 w-64 h-64 rounded-full bg-gradient-to-br from-teal-500/20 to-[#00875a]/30 blur-3xl pointer-events-none" />
            <div className="absolute top-1/3 left-1/4 w-44 h-44 rounded-full bg-indigo-500/10 blur-2xl pointer-events-none" />

            <div className="max-w-4xl mx-auto px-4 sm:px-6 relative z-10 space-y-4">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/10 border border-white/10 text-xs font-semibold text-emerald-300">
                <span>SmartSports Platform Access</span>
              </div>
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-tight">
                Sports Facility Management <br />
                <span className="text-[#00875a]">&amp; Revenue Optimization</span>
              </h1>
              <p className="text-sm sm:text-base text-slate-300 max-w-2xl mx-auto font-normal">
                Select your designated role to enter the platform. Choose between customer court booking services or facility operations and dynamic yield management.
              </p>
            </div>
          </section>

          {/* Role Selection Cards */}
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 -mt-16 pb-16 relative z-20 w-full">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Card 1: Customer Portal */}
              <div
                onClick={() => selectRole("customer")}
                className="bg-white rounded-3xl p-8 border border-slate-100 shadow-md hover:shadow-xl hover:border-emerald-200 transition-all duration-300 cursor-pointer flex flex-col justify-between group"
              >
                <div className="space-y-5">
                  <div className="flex items-center justify-between">
                    <div className="w-14 h-14 rounded-2xl bg-emerald-50 text-[#00875a] flex items-center justify-center font-bold shadow-2xs group-hover:scale-105 transition-transform">
                      <User className="w-7 h-7" />
                    </div>
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-[#00875a] border border-emerald-100">
                      Players &amp; Members
                    </span>
                  </div>

                  <div>
                    <h2 className="text-xl font-extrabold text-slate-900 group-hover:text-[#00875a] transition-colors">
                      Customer Portal
                    </h2>
                    <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                      Search court availability in real-time, reserve football and badminton slots, manage active bookings, and consult the booking assistant.
                    </p>
                  </div>

                  <div className="pt-2 border-t border-slate-100 space-y-2 text-xs text-slate-600 font-medium">
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-[#00875a]" />
                      <span>Real-time court availability and instant booking</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-[#00875a]" />
                      <span>Schedule filters by date, sport, and time window</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-[#00875a]" />
                      <span>Automated conversational booking assistant</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-[#00875a]" />
                      <span>Self-service booking management and cancellations</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    selectRole("customer");
                  }}
                  className="w-full mt-8 py-3.5 px-4 rounded-xl bg-[#00875a] hover:bg-[#00744d] text-white font-bold text-xs tracking-wider uppercase transition-all shadow-md flex items-center justify-center space-x-2 group-hover:shadow-lg"
                >
                  <span>Enter Customer Portal</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>

              {/* Card 2: Admin Console */}
              <div
                onClick={() => selectRole("admin")}
                className="bg-white rounded-3xl p-8 border border-slate-100 shadow-md hover:shadow-xl hover:border-slate-300 transition-all duration-300 cursor-pointer flex flex-col justify-between group"
              >
                <div className="space-y-5">
                  <div className="flex items-center justify-between">
                    <div className="w-14 h-14 rounded-2xl bg-slate-100 text-slate-900 flex items-center justify-center font-bold shadow-2xs group-hover:scale-105 transition-transform">
                      <ShieldCheck className="w-7 h-7" />
                    </div>
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border border-slate-200">
                      Facility Operations
                    </span>
                  </div>

                  <div>
                    <h2 className="text-xl font-extrabold text-slate-900 group-hover:text-slate-700 transition-colors">
                      Admin Console
                    </h2>
                    <p className="text-xs text-slate-500 mt-2 leading-relaxed">
                      Optimize court yield with automated dynamic pricing, approve rate recommendations with custom overrides, and monitor facility analytics.
                    </p>
                  </div>

                  <div className="pt-2 border-t border-slate-100 space-y-2 text-xs text-slate-600 font-medium">
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-slate-900" />
                      <span>Multi-factor dynamic yield and demand forecasting</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-slate-900" />
                      <span>Rate recommendation approvals and custom overrides</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-slate-900" />
                      <span>Facility occupancy and revenue breakdown analytics</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="w-4 h-4 text-slate-900" />
                      <span>Targeted customer outreach and notification audit log</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    selectRole("admin");
                  }}
                  className="w-full mt-8 py-3.5 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs tracking-wider uppercase transition-all shadow-md flex items-center justify-center space-x-2 group-hover:shadow-lg"
                >
                  <span>Enter Admin Console</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </div>

            {/* Bottom Status Indicator */}
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 border-t border-slate-200/60 pt-4 px-2">
              <div className="flex items-center space-x-2">
                <span
                  className={`w-2 h-2 rounded-full ${
                    backendOnline ? "bg-emerald-500" : "bg-rose-500"
                  }`}
                />
                <span>
                  Backend Service:{" "}
                  <strong className="text-slate-700">
                    {backendOnline ? "Connected (127.0.0.1:8000)" : "Offline"}
                  </strong>
                </span>
              </div>
              <div className="mt-2 sm:mt-0 flex items-center space-x-4">
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-[#00875a] transition-colors"
                >
                  FastAPI Swagger Documentation &rarr;
                </a>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col">
          {/* 2. HERO BANNER SECTION */}
          <section className="bg-gradient-to-r from-[#14192b] via-[#1c1d3b] to-[#121524] text-white pt-10 pb-20 relative overflow-hidden">
        {/* Subtle Decorative Ambient Elements */}
        <div className="absolute top-4 left-10 w-4 h-4 rounded-full bg-teal-400/40 blur-sm pointer-events-none" />
        <div className="absolute top-8 right-16 w-6 h-6 rounded-full bg-teal-300/30 blur-sm pointer-events-none" />
        <div className="absolute -bottom-10 right-20 w-48 h-48 rounded-full bg-gradient-to-br from-teal-500/20 to-[#00875a]/30 blur-2xl pointer-events-none" />
        <div className="absolute top-1/2 left-1/3 w-32 h-32 rounded-full bg-indigo-500/10 blur-2xl pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white mb-1">
                {activePortal === "customer"
                  ? "Court Reservations"
                  : "Operations & Revenue Management"}
              </h1>
              <div className="text-xs text-slate-400 flex items-center space-x-1.5 font-medium">
                <span>SmartSports</span>
                <span>&gt;</span>
                <span className="text-slate-200 capitalize">
                  {activePortal === "customer" ? "Bookings" : "Operations"}
                </span>
              </div>
            </div>

            <div className="text-xs font-semibold px-3 py-1 bg-white/10 backdrop-blur-md rounded-full text-slate-300 border border-white/10 w-fit">
              {activePortal === "customer" ? "Customer Portal" : "Admin Console"}
            </div>
          </div>
        </div>
      </section>

      {/* 3. FLOATING TAB NAVIGATION BAR */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-12 relative z-20">
        {activePortal === "customer" ? (
          /* Customer Navigation Tabs */
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { id: "dashboard", label: "Courts", icon: LayoutDashboard },
              { id: "bookings", label: "My Bookings", icon: Calendar },
              { id: "chat", label: "Booking Assistant", icon: MessageSquare },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = customerTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setCustomerTab(tab.id)}
                  className={`py-4 px-3 rounded-2xl flex flex-col items-center justify-center space-y-2 transition-all duration-200 shadow-sm border ${
                    isActive
                      ? "bg-[#00875a] text-white border-[#00875a] shadow-md shadow-emerald-900/20"
                      : "bg-white text-slate-700 hover:bg-slate-50 border-slate-100 hover:border-slate-200"
                  }`}
                >
                  <Icon
                    className={`w-5 h-5 ${
                      isActive ? "text-white" : "text-slate-600"
                    }`}
                  />
                  <span className="text-xs font-bold tracking-tight">
                    {tab.label}
                  </span>
                </button>
              );
            })}
          </div>
        ) : (
          /* Admin Navigation Tabs */
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { id: "revenue", label: "Pricing Strategy", icon: Zap },
              { id: "pricing", label: "Rate Approvals", icon: DollarSign },
              { id: "analytics", label: "Analytics", icon: Activity },
              { id: "notifications", label: "Notifications", icon: Send },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = adminTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setAdminTab(tab.id)}
                  className={`py-4 px-3 rounded-2xl flex flex-col items-center justify-center space-y-2 transition-all duration-200 shadow-sm border ${
                    isActive
                      ? "bg-slate-900 text-white border-slate-900 shadow-md shadow-slate-900/30"
                      : "bg-white text-slate-700 hover:bg-slate-50 border-slate-100 hover:border-slate-200"
                  }`}
                >
                  <Icon
                    className={`w-5 h-5 ${
                      isActive ? "text-white" : "text-slate-600"
                    }`}
                  />
                  <span className="text-xs font-bold tracking-tight">
                    {tab.label}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* 4. MAIN BODY CONTAINER */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full space-y-8 flex-1">
        {/* OVERVIEW METRICS (Row of 4 KPI Cards) */}
        <section className="bg-white rounded-2xl p-6 border border-slate-100 shadow-xs">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900">Overview</h2>
              <p className="text-xs text-slate-400">
                {activePortal === "customer"
                  ? "Summary of court availability and your account activity"
                  : "Current facility utilization and revenue performance"}
              </p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-600 rounded-md">
              {activePortal === "customer"
                ? `Customer #${customerId}`
                : "Operations Mode"}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Stat 1 */}
            <div className="bg-[#fcfdfd] border border-slate-100 rounded-xl p-4 flex items-center justify-between shadow-2xs">
              <div>
                <span className="text-2xl font-black text-slate-900 block leading-tight">
                  {adminSlots.length || 78}
                </span>
                <span className="text-[11px] font-semibold text-slate-400">
                  {activePortal === "customer" ? "Available Courts" : "Available Slots"}
                </span>
              </div>
              <div className="w-10 h-10 rounded-xl bg-cyan-50 text-cyan-600 flex items-center justify-center font-bold">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <rect width="18" height="18" x="3" y="3" rx="2" strokeWidth="2" />
                  <path d="M3 9h18M9 21V9" strokeWidth="2" />
                </svg>
              </div>
            </div>

            {/* Stat 2 */}
            <div className="bg-[#fcfdfd] border border-slate-100 rounded-xl p-4 flex items-center justify-between shadow-2xs">
              <div>
                <span className="text-2xl font-black text-slate-900 block leading-tight">
                  {activePortal === "customer"
                    ? customerBookings.length
                    : `${analytics?.overall_fill_rate || 68}%`}
                </span>
                <span className="text-[11px] font-semibold text-slate-400">
                  {activePortal === "customer"
                    ? "Active Bookings"
                    : "Fill Rate"}
                </span>
              </div>
              <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
                <Trophy className="w-5 h-5" />
              </div>
            </div>

            {/* Stat 3 */}
            <div className="bg-[#fcfdfd] border border-slate-100 rounded-xl p-4 flex items-center justify-between shadow-2xs">
              <div>
                <span className="text-2xl font-black text-slate-900 block leading-tight">
                  {activePortal === "customer"
                    ? `₹${customerBookings
                        .reduce((sum, b) => sum + (b.amount_paid || 0), 0)
                        .toLocaleString()}`
                    : `₹${analytics?.total_revenue?.toLocaleString() || "45,056"}`}
                </span>
                <span className="text-[11px] font-semibold text-slate-400">
                  {activePortal === "customer" ? "Total Paid" : "Gross Revenue"}
                </span>
              </div>
              <div className="w-10 h-10 rounded-xl bg-emerald-50 text-[#00875a] flex items-center justify-center font-bold">
                <CreditCard className="w-5 h-5" />
              </div>
            </div>

            {/* Stat 4 */}
            <div className="bg-[#fcfdfd] border border-slate-100 rounded-xl p-4 flex items-center justify-between shadow-2xs">
              <div>
                <span className="text-2xl font-black text-slate-900 block leading-tight">
                  {activePortal === "customer"
                    ? `${customerBookings.length * 2} hrs`
                    : pricingHistory.length}
                </span>
                <span className="text-[11px] font-semibold text-slate-400">
                  {activePortal === "customer" ? "Hours Booked" : "Rate Approvals"}
                </span>
              </div>
              <div className="w-10 h-10 rounded-xl bg-teal-50 text-[#00875a] flex items-center justify-center font-bold">
                <Activity className="w-5 h-5" />
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================= */}
        {/* VIEW A: CUSTOMER PORTAL */}
        {/* ========================================================= */}
        {activePortal === "customer" && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left 8 Columns */}
            <div className="lg:col-span-8 space-y-6">
              {/* TAB 1: COURTS & BOOKING */}
              {customerTab === "dashboard" && (
                <div className="space-y-6">
                  {/* Filter Panel */}
                  <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-xs space-y-5">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
                      <div>
                        <h3 className="font-bold text-slate-900 text-sm">
                          Court Availability
                        </h3>
                        <p className="text-xs text-slate-400">
                          Filter slots by date, sport, and schedule
                        </p>
                      </div>

                      {/* Quick Date Presets */}
                      <div className="flex items-center space-x-1.5">
                        {[
                          { label: "Today", date: "2026-09-20" },
                          { label: "Tomorrow", date: "2026-09-21" },
                          { label: "Sep 22", date: "2026-09-22" },
                          { label: "Sep 23", date: "2026-09-23" },
                        ].map((item) => (
                          <button
                            key={item.date}
                            onClick={() => setSelectedDate(item.date)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                              selectedDate === item.date
                                ? "bg-[#00875a] text-white shadow-xs"
                                : "bg-slate-50 text-slate-600 hover:bg-slate-100"
                            }`}
                          >
                            {item.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Filter Selectors Bar */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* Date */}
                      <div>
                        <label className="text-[11px] font-bold uppercase text-slate-400 block mb-1.5">
                          Date
                        </label>
                        <input
                          type="date"
                          min="2026-09-20"
                          max="2026-09-30"
                          value={selectedDate}
                          onChange={(e) => setSelectedDate(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold text-slate-800 focus:outline-none focus:border-emerald-500"
                        />
                      </div>

                      {/* Sport */}
                      <div>
                        <label className="text-[11px] font-bold uppercase text-slate-400 block mb-1.5">
                          Sport
                        </label>
                        <div className="flex space-x-1.5">
                          {["All", "Football", "Badminton"].map((s) => (
                            <button
                              key={s}
                              onClick={() => setSportFilter(s)}
                              className={`flex-1 py-2 text-xs font-semibold rounded-xl text-center transition-all ${
                                sportFilter === s
                                  ? "bg-[#00875a] text-white shadow-xs"
                                  : "bg-slate-50 text-slate-600 hover:bg-slate-100"
                              }`}
                            >
                              {s}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Time Window */}
                      <div>
                        <label className="text-[11px] font-bold uppercase text-slate-400 block mb-1.5">
                          Time of Day
                        </label>
                        <div className="flex space-x-1">
                          {[
                            { id: "All", label: "All" },
                            { id: "morning", label: "Morning" },
                            { id: "afternoon", label: "Afternoon" },
                            { id: "evening", label: "Evening" },
                          ].map((t) => (
                            <button
                              key={t.id}
                              onClick={() => setTimeFilter(t.id)}
                              className={`flex-1 py-2 text-xs font-semibold rounded-xl text-center transition-all ${
                                timeFilter === t.id
                                  ? "bg-slate-900 text-white shadow-xs"
                                  : "bg-slate-50 text-slate-600 hover:bg-slate-100"
                              }`}
                            >
                              {t.label}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Available Courts Listing */}
                  <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-xs space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                      <div>
                        <h3 className="text-base font-bold text-slate-900">
                          Available Courts
                        </h3>
                        <p className="text-xs text-slate-400">
                          {selectedDate} • {sportFilter}
                        </p>
                      </div>
                      <span className="text-xs font-bold px-2.5 py-1 bg-emerald-50 text-[#00875a] border border-emerald-100 rounded-full">
                        {slots.length} Available
                      </span>
                    </div>

                    {loadingSlots ? (
                      <div className="flex justify-center py-16 text-slate-400">
                        <RefreshCw className="w-5 h-5 animate-spin mr-2 text-[#00875a]" />
                        <span className="text-xs font-semibold">Loading courts...</span>
                      </div>
                    ) : slots.length === 0 ? (
                      <div className="text-center py-14 px-4 space-y-3">
                        <Calendar className="w-10 h-10 text-slate-300 mx-auto" />
                        <h4 className="font-bold text-slate-700 text-sm">
                          No courts available for this selection
                        </h4>
                        <p className="text-xs text-slate-400">
                          Please choose another date or reset filters.
                        </p>
                        <button
                          onClick={() => {
                            setTimeFilter("All");
                            setSportFilter("All");
                          }}
                          className="px-4 py-1.5 bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700 rounded-lg"
                        >
                          Reset Filters
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {slots.map((slot) => (
                          <div
                            key={slot.slot_id}
                            className="p-4 rounded-xl border border-slate-100 hover:border-emerald-200 hover:shadow-sm transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-[#fcfdfd]"
                          >
                            <div className="flex items-center space-x-3.5">
                              <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center font-bold text-slate-600 text-lg border border-slate-200">
                                {slot.sport === "Football" ? "⚽" : "🏸"}
                              </div>
                              <div>
                                <div className="flex items-center space-x-2">
                                  <h4 className="font-bold text-slate-900 text-sm">
                                    {slot.court_name}
                                  </h4>
                                  <span className="px-2 py-0.5 text-[10px] font-bold rounded-md bg-slate-100 text-slate-600">
                                    {slot.sport}
                                  </span>
                                </div>
                                <div className="flex items-center space-x-4 text-xs text-slate-400 mt-1">
                                  <span className="flex items-center space-x-1">
                                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                                    <span>{slot.date}</span>
                                  </span>
                                  <span className="flex items-center space-x-1 font-semibold text-slate-600">
                                    <Clock className="w-3.5 h-3.5 text-[#00875a]" />
                                    <span>
                                      {slot.start_time} - {slot.end_time}
                                    </span>
                                  </span>
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center justify-between sm:justify-end space-x-4 pt-2 sm:pt-0 border-t sm:border-0 border-slate-100">
                              <div className="text-right">
                                <span className="text-[10px] font-bold uppercase text-slate-400 block">
                                  Rate
                                </span>
                                <span className="text-base font-extrabold text-[#00875a]">
                                  ₹{slot.base_price.toLocaleString()}
                                </span>
                              </div>
                              <button
                                onClick={() => handleBookSlot(slot.slot_id, slot.base_price)}
                                className="px-4 py-2 rounded-xl text-xs font-bold bg-[#00875a] text-white hover:bg-[#00744d] transition-all shadow-xs"
                              >
                                Book Court
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 2: MY BOOKINGS */}
              {customerTab === "bookings" && (
                <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-xs space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        My Bookings
                      </h3>
                      <p className="text-xs text-slate-400">
                        Active reservations and booking history
                      </p>
                    </div>
                    <span className="text-xs font-semibold px-3 py-1 bg-slate-100 rounded-full text-slate-700">
                      Customer #{customerId}
                    </span>
                  </div>

                  {customerBookings.length === 0 ? (
                    <div className="text-center py-14 text-slate-400">
                      No reservations found.
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {customerBookings.map((b) => (
                        <div
                          key={b.booking_id}
                          className="p-4 rounded-xl border border-slate-100 hover:border-slate-200 transition-all flex items-center justify-between bg-[#fcfdfd]"
                        >
                          <div className="flex items-center space-x-3.5">
                            <div className="w-11 h-11 rounded-xl bg-slate-100 flex items-center justify-center font-bold text-slate-600 border border-slate-200">
                              {b.sport === "Football" ? "⚽" : "🏸"}
                            </div>
                            <div>
                              <div className="flex items-center space-x-2">
                                <h4 className="font-bold text-slate-900 text-sm">
                                  {b.court_name}
                                </h4>
                                <span
                                  className={`px-2 py-0.5 text-[10px] font-bold rounded-md ${
                                    b.status === "Confirmed"
                                      ? "bg-emerald-50 text-[#00875a] border border-emerald-100"
                                      : "bg-rose-50 text-rose-600 border border-rose-100"
                                  }`}
                                >
                                  {b.status}
                                </span>
                              </div>
                              <span className="text-xs text-slate-400 block mt-1">
                                Date: {b.date} | {b.start_time} - {b.end_time} | Paid: ₹
                                {b.amount_paid.toLocaleString()}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center space-x-3">
                            <span className="text-sm font-black text-slate-900">
                              ₹{b.amount_paid.toLocaleString()}
                            </span>
                            {b.status === "Confirmed" && (
                              <button
                                onClick={() => handleCancelBooking(b.booking_id)}
                                className="px-3 py-1.5 text-xs font-bold text-rose-600 border border-rose-200 hover:bg-rose-50 rounded-lg transition-colors"
                              >
                                Cancel Booking
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: BOOKING ASSISTANT */}
              {customerTab === "chat" && (
                <div className="bg-white rounded-2xl border border-slate-100 shadow-xs flex flex-col h-[600px] overflow-hidden">
                  <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                    <div className="flex items-center space-x-3">
                      <div className="w-9 h-9 rounded-xl bg-emerald-50 text-[#00875a] flex items-center justify-center font-bold">
                        <MessageSquare className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="font-bold text-slate-900 text-sm">
                          Booking Assistant
                        </h3>
                        <span className="text-[11px] text-[#00875a] font-semibold flex items-center">
                          <span className="w-1.5 h-1.5 rounded-full bg-[#00875a] mr-1.5 animate-pulse" />
                          Online
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex-1 p-5 overflow-y-auto space-y-3 bg-[#fafbfb]">
                    {chatMessages.map((msg, idx) => (
                      <div
                        key={idx}
                        className={`flex ${
                          msg.role === "user" ? "justify-end" : "justify-start"
                        }`}
                      >
                        <div
                          className={`max-w-[80%] rounded-2xl px-4 py-3 text-xs leading-relaxed whitespace-pre-wrap ${
                            msg.role === "user"
                              ? "bg-[#00875a] text-white rounded-br-none shadow-xs"
                              : "bg-white border border-slate-200/80 text-slate-800 rounded-bl-none shadow-xs"
                          }`}
                        >
                          {msg.content}
                        </div>
                      </div>
                    ))}
                    {chatLoading && (
                      <div className="flex justify-start">
                        <div className="bg-white border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-500 flex items-center space-x-2">
                          <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#00875a]" />
                          <span>Searching courts...</span>
                        </div>
                      </div>
                    )}
                  </div>

                  <form
                    onSubmit={handleSendMessage}
                    className="p-4 border-t border-slate-100 bg-white flex items-center space-x-3"
                  >
                    <input
                      type="text"
                      placeholder="Type a message (e.g. Find me a football court tomorrow afternoon)..."
                      value={inputMessage}
                      onChange={(e) => setInputMessage(e.target.value)}
                      className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs focus:outline-none focus:border-emerald-500 text-slate-900"
                    />
                    <button
                      type="submit"
                      disabled={chatLoading || !inputMessage.trim()}
                      className="px-5 py-2.5 rounded-xl bg-[#00875a] hover:bg-[#00744d] text-white font-bold text-xs transition-all flex items-center space-x-1.5 shadow-xs disabled:opacity-50"
                    >
                      <span>Send</span>
                      <Send className="w-3.5 h-3.5" />
                    </button>
                  </form>
                </div>
              )}
            </div>

            {/* Right 4 Columns */}
            <div className="lg:col-span-4 space-y-6">
              {/* Wallet Card */}
              <div className="bg-gradient-to-br from-[#00875a] to-[#016845] rounded-2xl p-6 text-white shadow-md relative overflow-hidden">
                <div className="absolute -bottom-10 -right-10 w-40 h-40 rounded-full bg-white/10 pointer-events-none" />
                <div className="absolute top-0 right-1/4 w-20 h-20 rounded-full bg-emerald-300/10 blur-lg pointer-events-none" />

                <div className="relative z-10 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-emerald-100">
                      Wallet Balance
                    </span>
                    <button
                      onClick={() => setCustomerTab("dashboard")}
                      className="px-3 py-1 bg-white/20 hover:bg-white/30 border border-white/30 rounded-lg text-xs font-bold text-white transition-all shadow-2xs"
                    >
                      + Book Court
                    </button>
                  </div>

                  <div>
                    <span className="text-3xl font-black tracking-tight block">
                      ₹4,500
                    </span>
                    <span className="text-[11px] text-emerald-200 mt-1 block">
                      Available account credits
                    </span>
                  </div>
                </div>
              </div>

              {/* Upcoming Bookings Widget */}
              <div className="bg-white rounded-2xl p-6 border border-slate-100 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">
                      Upcoming Bookings
                    </h3>
                    <p className="text-[11px] text-slate-400">
                      Confirmed court reservations
                    </p>
                  </div>
                  <span className="px-2 py-0.5 text-[11px] font-bold bg-slate-100 text-slate-700 rounded-md">
                    Confirmed
                  </span>
                </div>

                {customerBookings.filter((b) => b.status === "Confirmed").length === 0 ? (
                  <div className="p-4 rounded-xl bg-[#fcfdfd] border border-slate-100 text-center text-xs text-slate-400">
                    No upcoming bookings scheduled.
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {customerBookings
                      .filter((b) => b.status === "Confirmed")
                      .slice(0, 3)
                      .map((b) => (
                        <div
                          key={b.booking_id}
                          className="p-3 rounded-xl border border-slate-100 bg-[#fcfdfd] flex items-center justify-between"
                        >
                          <div className="flex items-center space-x-3">
                            <div className="w-9 h-9 rounded-xl bg-slate-100 flex items-center justify-center font-bold text-sm">
                              {b.sport === "Football" ? "⚽" : "🏸"}
                            </div>
                            <div>
                              <span className="font-bold text-xs text-slate-900 block">
                                {b.court_name}
                              </span>
                              <span className="text-[10px] text-slate-400">
                                {b.date} • {b.start_time} - {b.end_time}
                              </span>
                            </div>
                          </div>
                          <span className="text-xs font-extrabold text-[#00875a]">
                            ₹{b.amount_paid}
                          </span>
                        </div>
                      ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* VIEW B: ADMIN CONSOLE */}
        {/* ========================================================= */}
        {activePortal === "admin" && (
          <div className="space-y-6">
            {/* TAB 1: PRICING STRATEGY */}
            {adminTab === "revenue" && (
              <div className="space-y-6">
                <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-xs">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        Revenue Optimization
                      </h3>
                      <p className="text-xs text-slate-400">
                        Demand modeling and price recommendation
                      </p>
                    </div>

                    <div className="flex items-center space-x-2.5">
                      <select
                        value={selectedSlotId || ""}
                        onChange={(e) => setSelectedSlotId(parseInt(e.target.value))}
                        className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-semibold text-slate-800 focus:outline-none"
                      >
                        {adminSlots.map((s) => (
                          <option key={s.slot_id} value={s.slot_id}>
                            Slot #{s.slot_id} | {s.court_name} ({s.sport}) — {s.slot_date}
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={handleRunRevenueAgent}
                        className="px-5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs transition-all shadow-xs"
                      >
                        Analyze Slot
                      </button>
                    </div>
                  </div>
                </div>

                {revenueAnalysis && (
                  <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-xs space-y-5">
                    {/* Strategy Banner */}
                    <div className="bg-slate-900 text-white p-5 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-400 block mb-1">
                          Recommendation
                        </span>
                        <p className="text-xs text-slate-200 leading-relaxed max-w-2xl">
                          {revenueAnalysis.reasoning}
                        </p>
                      </div>
                      <span className="px-4 py-2 rounded-xl text-xs font-black bg-[#00875a] text-white shadow-sm w-fit">
                        {revenueAnalysis.action}
                      </span>
                    </div>

                    {/* Numbers Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                      <div className="bg-[#fcfdfd] p-4 rounded-xl border border-slate-100">
                        <span className="text-[11px] text-slate-400 block font-semibold">
                          Base Rate
                        </span>
                        <span className="text-lg font-bold text-slate-800">
                          ₹{revenueAnalysis.base_price}
                        </span>
                      </div>
                      <div className="bg-[#fcfdfd] p-4 rounded-xl border border-slate-100">
                        <span className="text-[11px] text-slate-400 block font-semibold">
                          Suggested Rate
                        </span>
                        <span className="text-lg font-extrabold text-[#00875a]">
                          ₹{revenueAnalysis.suggested_price}
                          <span className="text-xs ml-1 font-semibold text-slate-500">
                            ({revenueAnalysis.adjustment_percentage > 0 ? "+" : ""}
                            {revenueAnalysis.adjustment_percentage}%)
                          </span>
                        </span>
                      </div>
                      <div className="bg-[#fcfdfd] p-4 rounded-xl border border-slate-100">
                        <span className="text-[11px] text-slate-400 block font-semibold">
                          Projected Profit
                        </span>
                        <span className="text-lg font-bold text-slate-800">
                          ₹{revenueAnalysis.estimated_profit.toLocaleString()}
                        </span>
                      </div>
                      <div className="bg-[#fcfdfd] p-4 rounded-xl border border-slate-100">
                        <span className="text-[11px] text-slate-400 block font-semibold">
                          Profit Margin
                        </span>
                        <span className="text-lg font-bold text-slate-800">
                          {revenueAnalysis.profit_margin.toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    {/* Customers Cohort & Offer */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                      <div className="bg-slate-50/70 p-5 rounded-2xl border border-slate-200/70 space-y-3">
                        <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider flex items-center space-x-2">
                          <Users className="w-4 h-4 text-[#00875a]" />
                          <span>Target Audience</span>
                        </h4>
                        <div className="space-y-2">
                          {revenueAnalysis.target_customers.map((c, i) => (
                            <div
                              key={i}
                              className="p-3 bg-white rounded-xl border border-slate-200/70 flex items-center justify-between text-xs"
                            >
                              <div>
                                <span className="font-bold text-slate-800 block">
                                  {c.name}
                                </span>
                                <span className="text-[11px] text-slate-400">
                                  {c.customer_type} • {c.booking_frequency} bookings
                                </span>
                              </div>
                              <span className="px-2 py-1 bg-emerald-50 text-[#00875a] font-bold rounded text-[11px]">
                                Score: {Math.round(c.score)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="bg-slate-50/70 p-5 rounded-2xl border border-slate-200/70 space-y-3">
                        <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider flex items-center space-x-2">
                          <MessageSquare className="w-4 h-4 text-[#00875a]" />
                          <span>Notification Template</span>
                        </h4>
                        <pre className="p-4 bg-white rounded-xl border border-slate-200/70 text-xs text-slate-700 font-sans whitespace-pre-wrap leading-relaxed h-[180px] overflow-y-auto">
                          {revenueAnalysis.offer_message}
                        </pre>
                      </div>
                    </div>

                    <button
                      onClick={handleExecuteRevenueStrategy}
                      disabled={executingStrategy}
                      className="w-full py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs tracking-wider uppercase transition-all shadow-md disabled:opacity-50"
                    >
                      {executingStrategy
                        ? "Applying updates..."
                        : "Apply Rate & Send Notifications"}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: RATE APPROVALS */}
            {adminTab === "pricing" && (
              <div className="space-y-6">
                <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-xs flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-center space-x-3">
                    <span className="text-xs font-bold text-slate-400">Sport:</span>
                    {["All", "Football", "Badminton"].map((s) => (
                      <button
                        key={s}
                        onClick={() => setPricingSportFilter(s)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                          pricingSportFilter === s
                            ? "bg-slate-900 text-white"
                            : "bg-slate-50 text-slate-600 hover:bg-slate-100"
                        }`}
                      >
                        {s}
                      </button>
                    ))}
                  </div>

                  <div className="flex items-center space-x-3">
                    <span className="text-xs font-bold text-slate-400">Demand:</span>
                    {["All", "HIGH", "MEDIUM", "LOW"].map((d) => (
                      <button
                        key={d}
                        onClick={() => setPricingDemandFilter(d)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                          pricingDemandFilter === d
                            ? "bg-[#00875a] text-white"
                            : "bg-slate-50 text-slate-600 hover:bg-slate-100"
                        }`}
                      >
                        {d}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Review Card */}
                {selectedPricingSlot && (
                  <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-xs space-y-4">
                    <div className="flex items-center justify-between">
                      <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider">
                        Slot #{selectedPricingSlot.slot_id} — {selectedPricingSlot.court_name}
                      </h4>
                      <span className="text-xs text-slate-400">
                        {selectedPricingSlot.date} • {selectedPricingSlot.start_time} - {selectedPricingSlot.end_time}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                      <div className="bg-slate-50 p-3 rounded-xl">
                        <span className="text-[11px] text-slate-400 block font-semibold">Demand</span>
                        <span className="font-bold text-xs text-slate-800">
                          {selectedPricingSlot.demand}
                        </span>
                      </div>
                      <div className="bg-slate-50 p-3 rounded-xl">
                        <span className="text-[11px] text-slate-400 block font-semibold">Base Rate</span>
                        <span className="font-bold text-xs text-slate-800">
                          ₹{selectedPricingSlot.base_price}
                        </span>
                      </div>
                      <div className="bg-slate-50 p-3 rounded-xl">
                        <span className="text-[11px] text-slate-400 block font-semibold">Adjustment</span>
                        <span className="font-bold text-xs text-[#00875a]">
                          {selectedPricingSlot.adjustment_percentage > 0 ? "+" : ""}
                          {selectedPricingSlot.adjustment_percentage}%
                        </span>
                      </div>
                      <div className="bg-slate-50 p-3 rounded-xl">
                        <span className="text-[11px] text-slate-400 block font-semibold">Suggested Rate</span>
                        <span className="font-extrabold text-xs text-slate-900">
                          ₹{selectedPricingSlot.suggested_price}
                        </span>
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 pt-2">
                      <button
                        onClick={() =>
                          handleApprovePrice(
                            selectedPricingSlot.slot_id,
                            selectedPricingSlot.suggested_price,
                            "Approved"
                          )
                        }
                        className="px-4 py-2 bg-[#00875a] hover:bg-[#00744d] text-white font-bold text-xs rounded-xl transition-all shadow-xs"
                      >
                        Approve (₹{selectedPricingSlot.suggested_price})
                      </button>
                      <button
                        onClick={() =>
                          handleApprovePrice(
                            selectedPricingSlot.slot_id,
                            selectedPricingSlot.base_price,
                            "Kept Base"
                          )
                        }
                        className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition-all"
                      >
                        Keep Base Rate
                      </button>

                      <div className="flex items-center space-x-2 ml-auto">
                        <input
                          type="number"
                          placeholder="Custom Rate ₹"
                          value={customPriceInput}
                          onChange={(e) => setCustomPriceInput(e.target.value)}
                          className="w-32 bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-xs text-slate-800 focus:outline-none"
                        />
                        <button
                          onClick={() => {
                            const val = parseFloat(customPriceInput);
                            if (val > 0) {
                              handleApprovePrice(
                                selectedPricingSlot.slot_id,
                                val,
                                "Modified"
                              );
                              setCustomPriceInput("");
                            }
                          }}
                          className="px-4 py-2 bg-slate-900 text-white font-bold text-xs rounded-xl hover:bg-slate-800"
                        >
                          Apply Custom
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* Table */}
                <div className="bg-white rounded-2xl border border-slate-100 shadow-xs overflow-hidden">
                  <div className="px-5 py-3.5 border-b border-slate-100">
                    <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider">
                      Rate Recommendations ({filteredPricing.length} slots)
                    </h4>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs text-slate-700">
                      <thead className="bg-[#fcfdfd] text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-100 text-[11px]">
                        <tr>
                          <th className="p-3.5">Slot ID</th>
                          <th className="p-3.5">Court</th>
                          <th className="p-3.5">Sport</th>
                          <th className="p-3.5">Schedule</th>
                          <th className="p-3.5">Demand</th>
                          <th className="p-3.5">Base Rate</th>
                          <th className="p-3.5">Suggested Rate</th>
                          <th className="p-3.5 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {filteredPricing.slice(0, 15).map((p) => (
                          <tr key={p.slot_id} className="hover:bg-slate-50 transition-colors">
                            <td className="p-3.5 font-bold text-slate-400">#{p.slot_id}</td>
                            <td className="p-3.5 text-slate-900 font-bold">{p.court_name}</td>
                            <td className="p-3.5">{p.sport}</td>
                            <td className="p-3.5">
                              {p.date} ({p.start_time})
                            </td>
                            <td className="p-3.5">
                              <span
                                className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                                  p.demand === "HIGH"
                                    ? "bg-rose-50 text-rose-600"
                                    : p.demand === "LOW"
                                    ? "bg-amber-50 text-amber-600"
                                    : "bg-blue-50 text-blue-600"
                                }`}
                              >
                                {p.demand}
                              </span>
                            </td>
                            <td className="p-3.5">₹{p.base_price}</td>
                            <td className="p-3.5 font-bold text-[#00875a]">
                              ₹{p.suggested_price}
                            </td>
                            <td className="p-3.5 text-right">
                              <button
                                onClick={() => setSelectedPricingSlot(p)}
                                className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-bold"
                              >
                                Review
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: ANALYTICS */}
            {adminTab === "analytics" && analytics && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-xs space-y-4">
                  <h4 className="font-bold text-xs text-slate-900 uppercase tracking-wider">
                    Court Utilization
                  </h4>
                  <div className="space-y-3">
                    {analytics.fill_rate_by_court.map((c, i) => (
                      <div key={i} className="space-y-1">
                        <div className="flex justify-between text-xs text-slate-700 font-semibold">
                          <span>{c.court_name}</span>
                          <span>{c.fill_rate}%</span>
                        </div>
                        <div className="w-full bg-slate-100 rounded-full h-2">
                          <div
                            className="bg-[#00875a] h-2 rounded-full"
                            style={{ width: `${c.fill_rate}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-xs space-y-4">
                  <h4 className="font-bold text-xs text-slate-900 uppercase tracking-wider">
                    Revenue by Court
                  </h4>
                  <div className="space-y-3">
                    {analytics.revenue_by_court.map((c, i) => (
                      <div key={i} className="space-y-1">
                        <div className="flex justify-between text-xs text-slate-700 font-semibold">
                          <span>{c.court_name}</span>
                          <span>₹{c.revenue.toLocaleString()}</span>
                        </div>
                        <div className="w-full bg-slate-100 rounded-full h-2">
                          <div
                            className="bg-slate-800 h-2 rounded-full"
                            style={{
                              width: `${(c.revenue / analytics.total_revenue) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: NOTIFICATIONS LOG */}
            {adminTab === "notifications" && (
              <div className="bg-white rounded-2xl border border-slate-100 shadow-xs overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100">
                  <h4 className="font-bold text-sm text-slate-900">
                    Notification Log ({notifications.length} records)
                  </h4>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-700">
                    <thead className="bg-[#fcfdfd] text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-100 text-[11px]">
                      <tr>
                        <th className="p-3.5">ID</th>
                        <th className="p-3.5">Recipient</th>
                        <th className="p-3.5">Court</th>
                        <th className="p-3.5">Channel</th>
                        <th className="p-3.5">Sent</th>
                        <th className="p-3.5">Message</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {notifications.map((n) => (
                        <tr key={n.notification_id} className="hover:bg-slate-50 transition-colors">
                          <td className="p-3.5 font-bold text-slate-400">#{n.notification_id}</td>
                          <td className="p-3.5 font-bold text-slate-900">{n.recipient_name}</td>
                          <td className="p-3.5">{n.court_name}</td>
                          <td className="p-3.5 font-semibold text-[#00875a]">{n.channel}</td>
                          <td className="p-3.5 text-slate-400">{n.sent_at}</td>
                          <td className="p-3.5 max-w-xs truncate text-slate-500 font-mono text-[11px]">
                            {n.message}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
        </div>
      )}
    </div>
  );
}

