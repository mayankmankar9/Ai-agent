"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { doc, setDoc } from "firebase/firestore";
import { auth, db } from "@/lib/firebase";

export default function OnboardingForm() {
  const router = useRouter();

  const [formData, setFormData] = useState({
    name: "",
    age: "",
    gender: "male",
    height_cm: "",
    weight_kg: "",
    diet_type: "veg",
    dislikes: "",
    activity_level: "sedentary",
    goal: "bulk",
    tenure_months: "",
    target_weight: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleGoalClick = (goal: string) => {
    setFormData({ ...formData, goal });
  };

  const handleDietClick = (diet_type: string) => {
    setFormData({ ...formData, diet_type });
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const user = auth.currentUser;
    if (!user) return;

    const dataToSave = {
      ...formData,
      age: parseInt(formData.age),
      height_cm: parseFloat(formData.height_cm),
      weight_kg: parseFloat(formData.weight_kg),
      tenure_months: parseInt(formData.tenure_months),
      target_weight: formData.target_weight ? parseFloat(formData.target_weight) : null,
    };

    try {
      await setDoc(doc(db, "users", user.uid), dataToSave, { merge: true });
      console.log("✅ User profile saved to Firestore:", dataToSave);
      router.push("/dashboard");
    } catch (err) {
      console.error("❌ Firestore error:", err);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-6 space-y-4">
      <h1 className="text-2xl font-bold mb-4">Personalize Your Plan</h1>
      <input name="name" placeholder="Name" value={formData.name} onChange={handleChange} className="w-full border p-2 rounded" required />
      <input name="age" placeholder="Age" type="number" value={formData.age} onChange={handleChange} className="w-full border p-2 rounded" required />
      <input name="gender" placeholder="Gender" value={formData.gender} onChange={handleChange} className="w-full border p-2 rounded" required />
      <input name="height_cm" placeholder="Height (cm)" type="number" value={formData.height_cm} onChange={handleChange} className="w-full border p-2 rounded" required />
      <input name="weight_kg" placeholder="Weight (kg)" type="number" value={formData.weight_kg} onChange={handleChange} className="w-full border p-2 rounded" required />
      <input name="dislikes" placeholder="Dislikes (comma-separated)" value={formData.dislikes} onChange={handleChange} className="w-full border p-2 rounded" />
      <select name="activity_level" value={formData.activity_level} onChange={handleChange} className="w-full border p-2 rounded">
        <option value="sedentary">Sedentary</option>
        <option value="moderate">Moderate</option>
        <option value="active">Active</option>
      </select>

      <div>
        <p className="font-semibold">Select Goal:</p>
        <div className="flex gap-4 mt-2">
          {["cut", "bulk", "maintain"].map((goal) => (
            <button
              key={goal}
              type="button"
              onClick={() => handleGoalClick(goal)}
              className={`px-4 py-2 rounded ${formData.goal === goal ? "bg-blue-600 text-white" : "bg-gray-200"}`}
            >
              {goal.charAt(0).toUpperCase() + goal.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div>
        <p className="font-semibold">Select Diet Type:</p>
        <div className="flex gap-4 mt-2">
          {["veg", "non-veg"].map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => handleDietClick(type)}
              className={`px-4 py-2 rounded ${formData.diet_type === type ? "bg-green-600 text-white" : "bg-gray-200"}`}
            >
              {type === "veg" ? "Vegetarian" : "Non-Vegetarian"}
            </button>
          ))}
        </div>
      </div>

      <input
        name="tenure_months"
        placeholder="Tenure (months)"
        type="number"
        value={formData.tenure_months}
        onChange={handleChange}
        className="w-full border p-2 rounded"
        required
      />

      <input
        name="target_weight"
        placeholder="Target Weight (kg) [optional]"
        type="number"
        value={formData.target_weight}
        onChange={handleChange}
        className="w-full border p-2 rounded"
      />

      <button type="submit" className="w-full bg-blue-600 text-white py-2 px-4 rounded">
        Save and Continue
      </button>
    </form>
  );
}
