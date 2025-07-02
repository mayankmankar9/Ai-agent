'use client';

import { useState } from 'react';
import { db, auth } from '@/lib/firebase';
import { doc, setDoc } from 'firebase/firestore';
import { useRouter } from 'next/navigation';

export default function ProfilePage() {
  const [goal, setGoal] = useState('bulk');
  const [dietType, setDietType] = useState('veg');
  const [dislikes, setDislikes] = useState('');
  const router = useRouter();

  const saveProfile = async () => {
    const user = auth.currentUser;
    if (!user) return;
    await setDoc(doc(db, 'users', user.uid), {
      goal,
      diet_type: dietType,
      dislikes,
    });
    router.push('/dashboard');
  };

  return (
    <div className="p-6 max-w-md mx-auto">
      <h2 className="text-xl font-bold mb-4">Set up your diet preferences</h2>
      <select value={goal} onChange={(e) => setGoal(e.target.value)} className="w-full mb-3 p-2">
        <option value="bulk">Bulk</option>
        <option value="cut">Cut</option>
        <option value="maintain">Maintain</option>
      </select>
      <select value={dietType} onChange={(e) => setDietType(e.target.value)} className="w-full mb-3 p-2">
        <option value="veg">Vegetarian</option>
        <option value="non-veg">Non-Vegetarian</option>
      </select>
      <input type="text" placeholder="Any dislikes?" value={dislikes} onChange={(e) => setDislikes(e.target.value)} className="w-full p-2 mb-4 border" />
      <button onClick={saveProfile} className="w-full bg-blue-600 text-white py-2 rounded">Save & Continue</button>
    </div>
  );
}
