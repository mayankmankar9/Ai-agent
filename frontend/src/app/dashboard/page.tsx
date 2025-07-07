"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import axios from "axios";
import { useRouter } from "next/navigation";

interface WeekPlan {
  week_number: number;
  response: string;
}

interface MonthPlan {
  month: number;
  weeks: WeekPlan[];
}

export default function DashboardPage() {
  const { user, loading, logout } = useAuth();
  const [userProfile, setUserProfile] = useState<any>(null);
  const [plans, setPlans] = useState<MonthPlan[]>([]);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMonth, setSelectedMonth] = useState<number | null>(null);
  const [selectedWeek, setSelectedWeek] = useState<number | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!user) return;

    const fetchUserProfile = async () => {
      try {
        const token = await user.getIdToken();
        const res = await axios.get(`http://localhost:8000/user/${user.uid}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUserProfile(res.data);
      } catch (err) {
        console.error("Failed to fetch user profile:", err);
        setError("Failed to fetch user profile. Please try again.");
      }
    };

    const fetchPlans = async () => {
      try {
        const token = await user.getIdToken();
        const res = await axios.get(`http://localhost:8000/plans/${user.uid}`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        const flatPlans = res.data.plans;
        const groupedByMonth = groupPlansByMonth(flatPlans);
        setPlans(groupedByMonth);
      } catch (err) {
        console.error("Failed to fetch saved plans:", err);
        setError("Could not load previous plans.");
      }
    };

    fetchUserProfile();
    fetchPlans();
  }, [user]);

  const groupPlansByMonth = (plans: any[]): MonthPlan[] => {
    const result: MonthPlan[] = [];
    const totalWeeks = plans.length;
    const totalMonths = Math.ceil(totalWeeks / 4);

    for (let m = 0; m < totalMonths; m++) {
      const monthWeeks = plans
        .filter(w => w.week_number >= m * 4 + 1 && w.week_number <= (m + 1) * 4)
        .sort((a, b) => a.week_number - b.week_number);
      if (monthWeeks.length > 0) {
        result.push({ month: m + 1, weeks: monthWeeks });
      }
    }

    return result;
  };

  const handleGeneratePlan = async () => {
    if (!user || !userProfile) return;
    setGenerating(true);
    setError(null);
    try {
      const token = await user.getIdToken();
      const currentWeek = plans.reduce((acc, month) => acc + month.weeks.length, 0) + 1;
      const query = `Generate my meal plan for weeks ${currentWeek}-${currentWeek + 3} based on my goal to ${userProfile.goal} from weight ${userProfile.weight_kg} to ${userProfile.target_weight} over ${userProfile.tenure_months} months`;

      const res = await axios.post(
        "http://localhost:8000/agent/query",
        { user_id: user.uid, query },
        { headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } }
      );

      const responseText = res.data.response || "No response received.";
      const weekChunks = responseText
        .split(/(?=Week\s+\d+)/i)
        .filter(Boolean)
        .map((chunk: string, i: number) => ({ week_number: currentWeek + i, response: chunk.trim() }));

      const newMonth = {
        month: Math.ceil(currentWeek / 4),
        weeks: weekChunks,
      };

      const updatedPlans = [...plans];
      const existingMonthIndex = updatedPlans.findIndex(m => m.month === newMonth.month);
      if (existingMonthIndex !== -1) {
        updatedPlans[existingMonthIndex].weeks.push(...newMonth.weeks);
      } else {
        updatedPlans.push(newMonth);
      }

      setPlans(updatedPlans);
    } catch (err) {
      console.error(err);
      setError("Failed to generate plan. Please try again.");
    } finally {
      setGenerating(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center h-screen text-xl">Loading user...</div>;
  if (!user) {
    return (
      <div className="flex flex-col items-center justify-center h-screen text-xl">
        <div>Please sign in.</div>
        <button
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded shadow hover:bg-blue-700"
          onClick={() => router.push("/login")}
        >
          Go to Login
        </button>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gray-100 py-8 px-4 flex flex-col items-center">
      <div className="w-full max-w-4xl">
        {userProfile && (
          <div className="bg-white rounded-xl shadow p-6 mb-6 border border-gray-200">
            <h2 className="text-2xl font-bold mb-4 text-blue-700">👤 Your Profile</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-gray-700 text-sm">
              <div><strong>Name:</strong> {userProfile.name}</div>
              <div><strong>Age:</strong> {userProfile.age}</div>
              <div><strong>Goal:</strong> {userProfile.goal}</div>
              <div><strong>Diet:</strong> {userProfile.diet_type}</div>
              <div><strong>Weight:</strong> {userProfile.weight_kg} kg</div>
              <div><strong>Target Weight:</strong> {userProfile.target_weight} kg</div>
              <div><strong>Tenure:</strong> {userProfile.tenure_months} months</div>
              <div><strong>Activity Level:</strong> {userProfile.activity_level}</div>
            </div>
            <div className="mt-4 flex gap-4">
              <button
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 shadow"
                onClick={handleGeneratePlan}
                disabled={generating}
              >
                {generating ? "Generating..." : `Generate Month ${plans.length + 1}`}
              </button>
              <button
                className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 shadow"
                onClick={logout}
              >
                Log out
              </button>
            </div>
            {error && <div className="mt-2 text-red-600 font-semibold">{error}</div>}
          </div>
        )}

        {plans.map((month) => (
          <div key={month.month} className="mb-6">
            <h3
              className="text-xl font-semibold text-gray-800 bg-yellow-200 px-4 py-2 rounded cursor-pointer"
              onClick={() => setSelectedMonth(month.month === selectedMonth ? null : month.month)}
            >
              📅 Month {month.month}
            </h3>
            {selectedMonth === month.month && (
              <div className="mt-2">
                {month.weeks.map((week) => (
                  <div key={week.week_number} className="mb-4">
                    <button
                      className="w-full text-left bg-gray-200 px-4 py-2 rounded hover:bg-gray-300 font-medium"
                      onClick={() => setSelectedWeek(week.week_number === selectedWeek ? null : week.week_number)}
                    >
                      Week {week.week_number}
                    </button>
                    {selectedWeek === week.week_number && (
                      <div className="bg-white border border-gray-300 p-4 rounded mt-2 whitespace-pre-wrap text-sm">
                        {week.response}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </main>
  );
}