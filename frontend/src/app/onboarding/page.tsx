"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { doc, setDoc } from "firebase/firestore";
import { db } from "@/lib/firebase";
import { useAuth } from "@/context/AuthContext";

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useAuth();

  const [formData, setFormData] = useState({
    name: "",
    age: "",
    gender: "male",
    height_cm: "",
    weight_kg: "",
    target_weight: "",
    diet_type: "veg",
    dislikes: "",
    activity_level: "moderate",
    goal: "cut",
    goal_intensity: "balanced",
    tenure_months: "", // auto-calculated
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;

    const { goal, weight_kg, target_weight, goal_intensity } = formData;
    const current = parseFloat(weight_kg);
    const target = parseFloat(target_weight);
    const delta = Math.abs(current - target);

    const intensityRate = {
      conservative: 0.25,
      balanced: 0.5,
      aggressive: 1.0,
    };

    const weeklyRate = intensityRate[goal_intensity as keyof typeof intensityRate] || 0.5;
    const weeks = weeklyRate > 0 ? Math.ceil(delta / weeklyRate) : 0;
    const months = Math.ceil(weeks / 4);

    if (goal === "maintain") {
      setFormData((prev) => ({
        ...prev,
        target_weight: prev.weight_kg,
        tenure_months: "4",
      }));
    } else {
      setFormData((prev) => ({
        ...prev,
        tenure_months: isNaN(months) ? "" : months.toString(),
      }));
    }
  }, [formData.goal, formData.weight_kg, formData.target_weight, formData.goal_intensity, user]);

  const handleChange = (e: any) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    if (!user?.uid) {
      setError("User not authenticated.");
      setSaving(false);
      return;
    }

    // Simple required field check
    for (const key of ["name", "age", "height_cm", "weight_kg", "target_weight", "tenure_months"]) {
      if (!formData[key as keyof typeof formData]) {
        setError("Please fill all required fields.");
        setSaving(false);
        return;
      }
    }

    const uid = user.uid;

    const parsedData = {
      ...formData,
      age: parseInt(formData.age),
      height_cm: parseFloat(formData.height_cm),
      weight_kg: parseFloat(formData.weight_kg),
      target_weight: parseFloat(formData.target_weight),
      tenure_months: parseInt(formData.tenure_months),
    };

    try {
      await setDoc(doc(db, "users", uid), parsedData, { merge: true });
      router.push("/dashboard");
    } catch (e) {
      setError("Failed to save profile. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="text-3xl font-bold mb-6">🎯 Let's Build Your Plan</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input name="name" type="text" placeholder="Full Name" value={formData.name} onChange={handleChange} className="w-full border p-2 rounded" required />
        <input name="age" type="number" placeholder="Age" value={formData.age} onChange={handleChange} className="w-full border p-2 rounded" required />
        <select name="gender" value={formData.gender} onChange={handleChange} className="w-full border p-2 rounded">
          <option value="male">Male</option>
          <option value="female">Female</option>
          <option value="other">Other</option>
        </select>
        <input name="height_cm" type="number" placeholder="Height (cm)" value={formData.height_cm} onChange={handleChange} className="w-full border p-2 rounded" required />
        <input name="weight_kg" type="number" placeholder="Current Weight (kg)" value={formData.weight_kg} onChange={handleChange} className="w-full border p-2 rounded" required />
        <input name="target_weight" type="number" placeholder="Target Weight (kg)" value={formData.target_weight} onChange={handleChange} className="w-full border p-2 rounded" required />

        <select name="diet_type" value={formData.diet_type} onChange={handleChange} className="w-full border p-2 rounded">
          <option value="veg">Vegetarian</option>
          <option value="non-veg">Non-Vegetarian</option>
        </select>

        <select name="activity_level" value={formData.activity_level} onChange={handleChange} className="w-full border p-2 rounded">
          <option value="sedentary">Sedentary</option>
          <option value="moderate">Moderate</option>
          <option value="very active">Very Active</option>
        </select>

        <input name="dislikes" type="text" placeholder="Dislikes (comma separated)" value={formData.dislikes} onChange={handleChange} className="w-full border p-2 rounded" />

        <select name="goal" value={formData.goal} onChange={handleChange} className="w-full border p-2 rounded">
          <option value="cut">Cut</option>
          <option value="bulk">Bulk</option>
          <option value="maintain">Maintain</option>
        </select>

        <select name="goal_intensity" value={formData.goal_intensity} onChange={handleChange} className="w-full border p-2 rounded">
          <option value="conservative">Conservative</option>
          <option value="balanced">Balanced</option>
          <option value="aggressive">Aggressive</option>
        </select>

        {formData.goal !== "maintain" && (
          <p className="text-gray-600">📅 Estimated Duration: <strong>{formData.tenure_months} months</strong></p>
        )}

        {error && <div className="text-red-600 font-semibold">{error}</div>}

        <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700" disabled={saving}>
          {saving ? "Saving..." : "Save & Continue →"}
        </button>
      </form>
    </div>
  );
}
