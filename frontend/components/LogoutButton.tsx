"use client";

import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase";
import { setAccessToken } from "@/lib/api";

export default function LogoutButton() {
  const router = useRouter();

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    setAccessToken(null);
    router.push("/login");
    router.refresh();
  }

  return (
    <button
      onClick={handleLogout}
      className="text-xs font-mono px-2.5 h-7 rounded transition-colors hover:bg-white/10"
      style={{ color: "rgba(250,250,247,0.5)" }}
    >
      sair
    </button>
  );
}
