"use client";

import { useEffect, useState } from "react";
import { auth } from "@/lib/firebase";
import axios from "axios";
import { useRouter } from "next/navigation";
import {
  doc,
  getDoc,
  collection,
  getDocs,
  orderBy,
  query,
  addDoc,
  serverTimestamp,
} from "firebase/firestore";
import { db } from "@/lib/firebase";
import { signOut } from "firebase/auth";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

type Plan = {
  id: string;
  week: string;
  timestamp?: any;
  response?: string;
};

type Profile = {
  name?: string;
  goal?: string;
  diet_type?: string;
  dislikes?: string;
  height_cm?: number;
  weight_kg?: number;
  target_weight?: number;
  tenure_months?: number;
};

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState("");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [planHistory, setPlanHistory] = useState<Plan[]>([]);
  const [selectedWeek, setSelectedWeek] = useState<Plan | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      const user = auth.currentUser;
      if (!user) return router.push("/onboarding");
      const ref = doc(db, "users", user.uid);
      const snap = await getDoc(ref);
      if (snap.exists()) {
        setProfile(snap.data());
      }
    };

    const fetchPlans = async () => {
      const user = auth.currentUser;
      if (!user) return;
      const plansRef = collection(db, "users", user.uid, "plans");
      const q = query(plansRef, orderBy("timestamp", "desc"));
      const snap = await getDocs(q);
      const plans = snap.docs.map((doc, index) => ({
        id: doc.id,
        week: `Week ${snap.docs.length - index}`,
        ...doc.data()
      }));
      setPlanHistory(plans);
    };

    fetchProfile();
    fetchPlans();
  }, []);

  const handleGenerate = async () => {
    const user = auth.currentUser;
    if (!user) return;
    setLoading(true);
    try {
      const idToken = await user.getIdToken();
      const plansRef = collection(db, "users", user.uid, "plans");
      const existingPlans = await getDocs(plansRef);
      const existingCount = existingPlans.size;
      let newPlans: Plan[] = [];

      for (let i = 1; i <= 4; i++) {
        const weekNumber = existingCount + i;
        const res = await axios.post(
          "http://localhost:8000/ask",
          { query: `Generate meal plan for week ${weekNumber}.` },
          { headers: { Authorization: `Bearer ${idToken}` } }
        );
        const planData = {
          response: res.data.response,
          timestamp: serverTimestamp(),
          week: `Week ${weekNumber}`
        };
        await addDoc(plansRef, planData);
        newPlans.push({
          id: `new-${weekNumber}-${Date.now()}`,
          week: `Week ${weekNumber}`,
          response: res.data.response,
          // timestamp will be updated on reload
        });
      }

      // Reload plans from Firestore to get correct IDs and timestamps
      const updatedSnap = await getDocs(query(plansRef, orderBy("timestamp", "desc")));
      const updatedPlans = updatedSnap.docs.map((doc, index) => ({
        id: doc.id,
        week: `Week ${updatedSnap.docs.length - index}`,
        ...doc.data()
      }));
      setPlanHistory(updatedPlans);
    } catch (err) {
      console.error("❌ Failed to generate:", err);
      setResponse("Something went wrong.");
    }
    setLoading(false);
  };

  // Generate PDF as Blob URL for display and download
  const generatePDFDataUrl = (week: string, plan: string) => {
    const doc = new jsPDF();
    doc.setFontSize(16);
    doc.text(`Meal Plan - ${week}`, 14, 20);
    // Split plan into days
    const days = plan.split("\n\n📅 ").map((day, idx) => {
      const lines = day.split("\n");
      return {
        day: lines[0],
        meals: lines.slice(1).join("\n")
      };
    });
    autoTable(doc, {
      startY: 30,
      head: [["Day", "Meals"]],
      body: days.map(d => [d.day, d.meals]),
      styles: { cellWidth: 'wrap' },
      columnStyles: { 1: { cellWidth: 120 } },
    });
    return doc.output('dataurlstring');
  };

  // Download PDF for the selected week
  const downloadPDF = (week: string, plan: string) => {
    const doc = new jsPDF();
    doc.setFontSize(16);
    doc.text(`Meal Plan - ${week}`, 14, 20);
    const days = plan.split("\n\n📅 ").map((day, idx) => {
      const lines = day.split("\n");
      return {
        day: lines[0],
        meals: lines.slice(1).join("\n")
      };
    });
    autoTable(doc, {
      startY: 30,
      head: [["Day", "Meals"]],
      body: days.map(d => [d.day, d.meals]),
      styles: { cellWidth: 'wrap' },
      columnStyles: { 1: { cellWidth: 120 } },
    });
    doc.save(`${week.replace(" ", "_")}_plan.pdf`);
  };

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div className="flex justify-between items-center mb-4">
        <button
          onClick={() => router.push("/onboarding")}
          className="text-sm px-3 py-1 bg-yellow-500 text-white rounded shadow"
        >
          ✏️ Edit Profile
        </button>
        <button
          onClick={async () => {
            await signOut(auth);
            router.push("/login");
          }}
          className="text-sm px-3 py-1 bg-red-600 text-white rounded shadow"
        >
          🔒 Logout
        </button>
      </div>

      <h1 className="text-2xl font-bold">Welcome to your Dashboard</h1>

      {profile && (
        <div className="p-4 rounded border shadow bg-white">
          <h2 className="text-lg font-semibold mb-2">Profile Summary</h2>
          <ul className="text-sm space-y-1">
            <li>Name: {profile.name}</li>
            <li>Goal: {profile.goal}</li>
            <li>Diet Type: {profile.diet_type}</li>
            <li>Dislikes: {profile.dislikes || "None"}</li>
            <li>Height: {profile.height_cm} cm</li>
            <li>Weight: {profile.weight_kg} kg</li>
            <li>Target Weight: {profile.target_weight || "Not specified"}</li>
            <li>Tenure: {profile.tenure_months} months</li>
          </ul>
        </div>
      )}

      <button
        className="bg-blue-600 text-white px-4 py-2 rounded shadow"
        onClick={handleGenerate}
        disabled={loading}
      >
        {loading ? "Generating..." : "Generate Plan"}
      </button>

      {/* Week selection buttons after plans are generated */}
      {planHistory.length > 0 && (
        <div className="flex gap-2 mt-6">
          {planHistory.slice(0, 4).map((plan: Plan, idx: number) => (
            <button
              key={plan.id}
              className={`px-4 py-2 rounded shadow text-white font-semibold ${selectedWeek?.id === plan.id ? 'bg-blue-700' : 'bg-blue-500'}`}
              onClick={() => {
                setSelectedWeek(plan);
                setPdfUrl(generatePDFDataUrl(plan.week, plan.response ?? ""));
              }}
            >
              {`Week ${idx + 1}`}
            </button>
          ))}
        </div>
      )}

      {/* PDF display and download */}
      {selectedWeek && pdfUrl && (
        <div className="mt-6 border rounded shadow bg-white p-4">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-lg font-bold">{selectedWeek.week} Meal Plan (Preview)</h2>
            <button
              className="bg-green-600 text-white text-sm px-3 py-1 rounded shadow"
              onClick={() => downloadPDF(selectedWeek.week, selectedWeek.response ?? "")}
            >
              ⬇️ Download PDF
            </button>
          </div>
          <iframe
            src={pdfUrl}
            title="Meal Plan PDF Preview"
            width="100%"
            height="600px"
            className="border rounded"
          />
        </div>
      )}
    </div>
  );
}
