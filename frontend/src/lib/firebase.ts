import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getAnalytics, isSupported } from "firebase/analytics";

// ✅ Your Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyBb_rxMq1ijhfV05LT6jRPSa81yUZ_hrc8",
  authDomain: "ai-agent-b7185.firebaseapp.com",
  projectId: "ai-agent-b7185",
  storageBucket: "ai-agent-b7185.firebasestorage.app",
  messagingSenderId: "472675093859",
  appId: "1:472675093859:web:c038f8bf65c7ad3afcd756",
  measurementId: "G-J0NGJP39BF",
};

// ✅ Initialize Firebase app once
const app = initializeApp(firebaseConfig);

// ✅ Setup Auth and Firestore
const auth = getAuth(app);
const db = getFirestore(app);

// ✅ Only run getAnalytics in browser
if (typeof window !== "undefined") {
  isSupported().then((supported) => {
    if (supported) {
      getAnalytics(app);
    }
  });
}

// ✅ Export everything needed
export { auth, db };
