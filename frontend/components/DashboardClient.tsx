"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase";
import { getDashboard, setAccessToken, type Dashboard } from "@/lib/api";
import DashboardStats from "@/components/DashboardStats";
import RecentSessions from "@/components/RecentSessions";
import TrajectoryChart from "@/components/TrajectoryChart";

export default function DashboardClient() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);

  useEffect(() => {
    const supabase = createClient();

    async function fetchDashboard(token: string) {
      setAccessToken(token);
      try {
        const data = await getDashboard();
        setDashboard(data);
      } catch {}
    }

    // Busca sessão atual primeiro, sem esperar o listener
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.access_token) fetchDashboard(session.access_token);
    });

    // Também escuta mudanças (ex: refresh do token)
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.access_token) fetchDashboard(session.access_token);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (!dashboard) return null;

  return (
    <div className="flex flex-col gap-10">
      <DashboardStats dashboard={dashboard} />
      {dashboard.recent_sessions.length > 0 && (
        <RecentSessions sessions={dashboard.recent_sessions} />
      )}
      <TrajectoryChart />
    </div>
  );
}
