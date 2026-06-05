import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { getApplications } from "../api";
import type { Application, Status } from "../types";

type DailyApplicationCount = {
  date: string;
  count: number;
};

export default function StatsPage() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [status, setStatus] = useState<Status>({ loading: true, error: "" });

  useEffect(() => {
    loadApplications();
  }, []);

  async function loadApplications() {
    setStatus({ loading: true, error: "" });
    try {
      setApplications(await getApplications());
      setStatus({ loading: false, error: "" });
    } catch (error) {
      setStatus({ loading: false, error: getErrorMessage(error) });
    }
  }

  const data = useMemo(() => groupApplicationsByDay(applications), [applications]);
  const chartData = useMemo(() => data.map((item) => ({ ...item, label: formatDay(item.date) })), [data]);

  return (
    <section className="page-grid">
      <section className="card">
        <div className="section-heading">
          <h3>Applications per day</h3>
          {status.loading ? <span>Loading...</span> : <span>{applications.length} total</span>}
        </div>
        {status.error ? <p className="error-message">{status.error}</p> : null}

        {!status.loading && data.length === 0 ? <p className="empty-state">No applications yet.</p> : null}

        {!status.loading && data.length > 0 ? (
          <div className="chart-wrap">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData} margin={{ top: 12, right: 8, bottom: 0, left: -24 }}>
                <CartesianGrid stroke="rgb(79 70 229 / 14%)" vertical={false} />
                <XAxis dataKey="label" tickLine={false} axisLine={false} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: "rgb(79 70 229 / 8%)" }} />
                <Bar dataKey="count" name="Applications" fill="#4f46e5" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : null}
      </section>
    </section>
  );
}

function groupApplicationsByDay(applications: Application[]): DailyApplicationCount[] {
  const counts = new Map<string, number>();
  for (const application of applications) {
    counts.set(application.candidature_date, (counts.get(application.candidature_date) ?? 0) + 1);
  }

  const dates = [...counts.keys()].sort();
  if (dates.length === 0) {
    return [];
  }

  const days: DailyApplicationCount[] = [];
  const current = parseDate(dates[0]);
  const last = parseDate(dates[dates.length - 1]);

  while (current <= last) {
    const date = formatDate(current);
    days.push({ date, count: counts.get(date) ?? 0 });
    current.setUTCDate(current.getUTCDate() + 1);
  }

  return days;
}

function formatDay(date: string) {
  const [, month, day] = date.split("-");
  return `${day}/${month}`;
}

function parseDate(date: string) {
  const [year, month, day] = date.split("-").map(Number);
  return new Date(Date.UTC(year, month - 1, day));
}

function formatDate(date: Date) {
  return date.toISOString().slice(0, 10);
}

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Unexpected error";
}
