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

type WeekPlan = {
  week: number;
  plan: string;
  totals: { kcal: number; protein: number; carbs: number; fat: number };
  start_weight: number;
  end_weight: number;
  tdee: number;
  protein_goal: number;
};

type MultiWeekSummary = {
  total_kcal: number;
  total_protein: number;
  total_carbs: number;
  total_fat: number;
  start_weight: number;
  end_weight: number;
  weeks: number;
  analysis?: string;
  warning?: string;
};

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState("");
  const [profile, setProfile] = useState<Profile | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<WeekPlan | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [weeks, setWeeks] = useState<WeekPlan[]>([]);
  const [summary, setSummary] = useState<MultiWeekSummary | null>(null);
  const [endState, setEndState] = useState<{ weight: number; week_offset: number } | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      const user = auth.currentUser;
      if (!user) return router.push("/onboarding");
      const ref = doc(db, "users", user.uid);
      const snap = await getDoc(ref);
      if (snap.exists()) {
        const data = snap.data();
        // List all required fields here
        const requiredFields = [
          "goal", "diet_type", "weight_kg", "height_cm", "age", "gender", "activity_level", "tenure_months"
        ];
        const isComplete = requiredFields.every(field => data[field] !== undefined && data[field] !== null && data[field] !== "");
        if (!isComplete) {
          router.push("/onboarding");
          return;
        }
        setProfile(data);
      } else {
        router.push("/onboarding");
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
      const tenure = profile?.tenure_months ?? 1;
      // If weeks already exist, send endState to backend for continuous planning
      const payload: any = { tenure_months: tenure };
      if (weeks.length > 0 && endState) {
        payload.start_state = endState;
      }
      const res = await axios.post(
        "http://localhost:8000/multiweek-plan",
        payload,
        { headers: { Authorization: `Bearer ${idToken}` } }
      );
      if (res.data && res.data.weeks && res.data.summary && res.data.end_state) {
        // Append new weeks to existing weeks
        setWeeks(prev => [...prev, ...res.data.weeks]);
        setSummary(res.data.summary); // Optionally, you can merge summaries if needed
        setEndState(res.data.end_state);
        setSelectedWeek(null);
        setPdfUrl(null);
      } else {
        setWeeks([]);
        setSummary(null);
        setEndState(null);
      }
    } catch (err) {
      console.error("❌ Failed to generate:", err);
      setResponse("Something went wrong.");
    }
    setLoading(false);
  };

  // Generate PDF as Blob URL for display and download
  const generatePDFDataUrl = (
    week: WeekPlan,
    profile: Profile | null,
    summary: MultiWeekSummary | null,
    showCumulative: boolean
  ) => {
    const doc = new jsPDF();
    // User Profile Section
    doc.setFontSize(14);
    doc.setTextColor(33, 37, 41);
    doc.text("User Profile", 14, 18);
    doc.setFontSize(11);
    doc.setTextColor(80, 80, 80);
    let y = 24;
    if (profile) {
      const profileLines = [
        `Name: ${profile.name ?? "-"}`,
        `Goal: ${profile.goal ?? "-"}`,
        `Diet Type: ${profile.diet_type ?? "-"}`,
        `Dislikes: ${profile.dislikes ?? "None"}`,
        `Height: ${profile.height_cm ?? "-"} cm`,
        `Weight: ${profile.weight_kg ?? "-"} kg`,
        `Target Weight: ${profile.target_weight ?? "-"}`,
        `Tenure: ${profile.tenure_months ?? "-"} months`,
      ];
      profileLines.forEach(line => {
        doc.text(line, 14, y);
        y += 6;
      });
    }
    y += 2;
    // Section Header
    doc.setFontSize(16);
    doc.setTextColor(30, 64, 175);
    doc.text(`Meal Plan - Week ${week.week}`, 14, y);
    y += 8;
    // Table of meals
    const days = week.plan.split("\n\n📅 ").map((day, idx) => {
      const lines = day.split("\n");
      return {
        day: lines[0],
        meals: lines.slice(1).join("\n")
      };
    });
    autoTable(doc, {
      startY: y,
      head: [["Day", "Meals"]],
      body: days.map(d => [d.day, d.meals]),
      styles: { cellWidth: 'wrap', fontSize: 10 },
      headStyles: { fillColor: [30, 64, 175], textColor: 255, fontStyle: 'bold' },
      alternateRowStyles: { fillColor: [240, 245, 255] },
      columnStyles: { 1: { cellWidth: 120 } },
    });
    y = (doc as any).lastAutoTable.finalY + 8;
    // Weekly Summary
    doc.setFontSize(13);
    doc.setTextColor(30, 64, 175);
    doc.text("Weekly Summary", 14, y);
    y += 6;
    doc.setFontSize(11);
    doc.setTextColor(60, 60, 60);
    doc.setFillColor(232, 240, 254);
    doc.rect(14, y - 5, 180, 28, 'F');
    doc.text(`Total Calories: ${week.totals.kcal.toFixed(1)} kcal`, 18, y + 3);
    doc.text(`Total Protein: ${week.totals.protein.toFixed(1)} g`, 70, y + 3);
    doc.text(`Total Carbs: ${week.totals.carbs.toFixed(1)} g`, 18, y + 11);
    doc.text(`Total Fat: ${week.totals.fat.toFixed(1)} g`, 70, y + 11);
    doc.text(`Start Weight: ${week.start_weight.toFixed(2)} kg`, 18, y + 19);
    doc.text(`End Weight: ${week.end_weight.toFixed(2)} kg`, 70, y + 19);
    y += 32;
    // Cumulative Summary (last week only)
    if (showCumulative && summary) {
      doc.setFontSize(13);
      doc.setTextColor(30, 64, 175);
      doc.text("Cumulative Summary", 14, y);
      y += 6;
      doc.setFontSize(11);
      doc.setTextColor(60, 60, 60);
      doc.setFillColor(220, 252, 231);
      doc.rect(14, y - 5, 180, 28, 'F');
      doc.text(`Total Calories: ${summary.total_kcal.toFixed(1)} kcal`, 18, y + 3);
      doc.text(`Total Protein: ${summary.total_protein.toFixed(1)} g`, 70, y + 3);
      doc.text(`Total Carbs: ${summary.total_carbs.toFixed(1)} g`, 18, y + 11);
      doc.text(`Total Fat: ${summary.total_fat.toFixed(1)} g`, 70, y + 11);
      doc.text(`Start Weight: ${summary.start_weight.toFixed(2)} kg`, 18, y + 19);
      doc.text(`End Weight: ${summary.end_weight.toFixed(2)} kg`, 70, y + 19);
    }
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

      {/* Nutrition Analysis and Warning */}
      {summary && (
        <div className="p-4 rounded border shadow bg-blue-50 text-blue-900">
          {summary.analysis && (
            <div className="mb-2 whitespace-pre-line">
              <strong>Nutrition Plan Analysis:</strong>
              <div>{summary.analysis}</div>
            </div>
          )}
          {summary.warning && (
            <div className="mb-2 text-red-700">
              <strong>Warning:</strong> {summary.warning}
            </div>
          )}
        </div>
      )}

      {/* Week selection buttons after plans are generated */}
      {weeks.length > 0 && (
        <div className="flex gap-2 mt-6">
          {weeks.map((week, idx) => (
            <button
              key={week.week}
              className={`px-4 py-2 rounded shadow text-white font-semibold ${selectedWeek?.week === week.week ? 'bg-blue-700' : 'bg-blue-500'}`}
              onClick={() => {
                setSelectedWeek(week);
                setPdfUrl(generatePDFDataUrl(week, profile, summary, idx === weeks.length - 1));
              }}
            >
              {`Week ${week.week}`}
            </button>
          ))}
        </div>
      )}

      {/* PDF display and download */}
      {selectedWeek && pdfUrl && (
        <div className="mt-6 border rounded shadow bg-white p-4">
          <div className="flex justify-between items-center mb-2">
            <h2 className="text-lg font-bold">Week {selectedWeek.week} Meal Plan (Preview)</h2>
            <button
              className="bg-green-600 text-white text-sm px-3 py-1 rounded shadow"
              onClick={() => {
                // Download PDF for this week
                const doc = new jsPDF();
                // ...repeat the same logic as generatePDFDataUrl, but use doc.save(...)
                // For brevity, you can refactor this into a shared function
              }}
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
