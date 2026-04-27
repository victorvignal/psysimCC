"use client";

import { useEffect, useState } from "react";
import { getDashboard, type Dashboard } from "@/lib/api";
import DashboardStats from "@/components/DashboardStats";
import RecentSessions from "@/components/RecentSessions";
import TrajectoryChart from "@/components/TrajectoryChart";

export default function DashboardClient() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);

  useEffect(() => {
    getDashboard().then(setDashboard).catch(() => {});
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
