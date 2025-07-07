"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { collection, getDocs } from "firebase/firestore";
import { db } from "../../lib/firebase";

interface ProgressEntry {
  date: string;
  weight: number;
  notes?: string;
}

export default function ProgressPage() {
  const { user, loading } = useAuth();
  const [progress, setProgress] = useState<ProgressEntry[]>([]);
  const [loadingProgress, setLoadingProgress] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;

    const fetchProgress = async () => {
      setLoadingProgress(true);
      try {
        const progressRef = collection(db, "users", user.uid, "progress");
        const snapshot = await getDocs(progressRef);
        const data: ProgressEntry[] = [];
        snapshot.forEach((doc) => {
          const docData = doc.data();
          if (docData.weight !== undefined && docData.date !== undefined) {
            data.push(docData as ProgressEntry);
          }
        });

        // Sort progress by date ascending
        data.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
        setProgress(data);
      } catch (e) {
        console.error(e);
        setError("Failed to load progress data.");
      } finally {
        setLoadingProgress(false);
      }
    };

    fetchProgress();
  }, [user]);

  if (loading) return <p>Loading user...</p>;
  if (!user) return <p>Please sign in to view your progress.</p>;

  return (
    <main>
      <h1>Your Progress</h1>
      {loadingProgress && <p>Loading progress data...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {progress.length === 0 && !loadingProgress && <p>No progress data available yet.</p>}

      <ul>
        {progress.map(({ date, weight, notes }, i) => (
          <li key={i}>
            <strong>{new Date(date).toLocaleDateString()}</strong>: {weight.toFixed(1)} kg{" "}
            {notes && <em>- {notes}</em>}
          </li>
        ))}
      </ul>
    </main>
  );
}
