"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import { doc, getDoc, setDoc } from "firebase/firestore";
import { db } from "../../lib/firebase";

interface UserProfile {
  name?: string;
  age?: number;
  gender?: "male" | "female" | "other";
  height_cm?: number;
  weight_kg?: number;
  diet_type?: "veg" | "non-veg";
  dislikes?: string;
  activity_level?: "sedentary" | "moderate" | "very active";
  goal?: "cut" | "bulk" | "maintain";
  goal_intensity?: "conservative" | "balanced" | "aggressive";
  tenure_months?: number;
  target_weight?: number;
}

export default function ProfilePage() {
  const { user, loading } = useAuth();
  const [profile, setProfile] = useState<UserProfile>({});
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!user) return;

    const fetchProfile = async () => {
      setLoadingProfile(true);
      try {
        const docRef = doc(db, "users", user.uid);
        const docSnap = await getDoc(docRef);
        if (docSnap.exists()) {
          setProfile(docSnap.data() as UserProfile);
        }
      } catch (e) {
        console.error(e);
        setError("Failed to load profile.");
      } finally {
        setLoadingProfile(false);
      }
    };

    fetchProfile();
  }, [user]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setProfile((prev) => ({
      ...prev,
      [name]:
        ["age", "height_cm", "weight_kg", "tenure_months", "target_weight"].includes(name)
          ? Number(value)
          : value,
    }));
  };

  const handleSave = async () => {
    if (!user) return;
    setSaving(true);
    setError(null);

    // Simple required field check
    for (const key of ["name", "age", "height_cm", "weight_kg", "target_weight", "tenure_months"]) {
      if (!profile[key as keyof UserProfile]) {
        setError("Please fill all required fields.");
        setSaving(false);
        return;
      }
    }

    try {
      await setDoc(doc(db, "users", user.uid), profile, { merge: true });
      alert("✅ Profile saved successfully.");
    } catch (e) {
      console.error(e);
      setError("Failed to save profile.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p>Loading user...</p>;
  if (!user) return <p>Please sign in to view your profile.</p>;

  return (
    <main style={{ padding: "2rem", maxWidth: "600px", margin: "auto" }}>
      <h1>Your Profile</h1>

      {loadingProfile && <p>Loading profile...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <label>
          Name:
          <input name="name" value={profile.name || ""} onChange={handleChange} />
        </label>

        <label>
          Age:
          <input type="number" name="age" value={profile.age || 0} onChange={handleChange} />
        </label>

        <label>
          Gender:
          <select name="gender" value={profile.gender || "male"} onChange={handleChange}>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </label>

        <label>
          Height (cm):
          <input type="number" name="height_cm" value={profile.height_cm || 0} onChange={handleChange} />
        </label>

        <label>
          Weight (kg):
          <input type="number" name="weight_kg" value={profile.weight_kg || 0} onChange={handleChange} />
        </label>

        <label>
          Diet Type:
          <select name="diet_type" value={profile.diet_type || "veg"} onChange={handleChange}>
            <option value="veg">Vegetarian</option>
            <option value="non-veg">Non-Vegetarian</option>
          </select>
        </label>

        <label>
          Dislikes:
          <textarea name="dislikes" value={profile.dislikes || ""} onChange={handleChange} rows={2} />
        </label>

        <label>
          Activity Level:
          <select name="activity_level" value={profile.activity_level || "moderate"} onChange={handleChange}>
            <option value="sedentary">Sedentary</option>
            <option value="moderate">Moderate</option>
            <option value="very active">Very Active</option>
          </select>
        </label>

        <label>
          Goal:
          <select name="goal" value={profile.goal || "maintain"} onChange={handleChange}>
            <option value="cut">Cutting</option>
            <option value="bulk">Bulking</option>
            <option value="maintain">Maintain</option>
          </select>
        </label>

        <label>
          Goal Intensity:
          <select name="goal_intensity" value={profile.goal_intensity || "balanced"} onChange={handleChange}>
            <option value="conservative">Conservative</option>
            <option value="balanced">Balanced</option>
            <option value="aggressive">Aggressive</option>
          </select>
        </label>

        <label>
          Tenure (months):
          <input type="number" name="tenure_months" value={profile.tenure_months || 3} onChange={handleChange} />
        </label>

        <label>
          Target Weight (kg):
          <input type="number" name="target_weight" value={profile.target_weight || 0} onChange={handleChange} />
        </label>

        {error && <div style={{ color: "red", fontWeight: "bold" }}>{error}</div>}

        <button onClick={handleSave} disabled={saving}>
          {saving ? "Saving..." : "Save Profile"}
        </button>
      </div>
    </main>
  );
}
