import { useEffect, useState } from "react";

import { getJobs, scrapeJobs, trackJob } from "../api";
import type { JobListing } from "../types";

type JobsStatus = {
  loading: boolean;
  error: string;
  message: string;
};

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobListing[]>([]);
  const [status, setStatus] = useState<JobsStatus>({ loading: true, error: "", message: "" });

  useEffect(() => {
    loadJobs();
  }, []);

  async function loadJobs() {
    setStatus({ loading: true, error: "", message: "" });
    try {
      setJobs(await getJobs());
      setStatus({ loading: false, error: "", message: "" });
    } catch (error) {
      setStatus({ loading: false, error: getErrorMessage(error), message: "" });
    }
  }

  async function handleScrape() {
    setStatus({ loading: true, error: "", message: "Scraping..." });
    try {
      const result = await scrapeJobs();
      setJobs(result.jobs);
      setStatus({ loading: false, error: "", message: `${result.imported} found.` });
    } catch (error) {
      setStatus({ loading: false, error: getErrorMessage(error), message: "" });
    }
  }

  async function handleTrack(job: JobListing) {
    try {
      await trackJob(job.id);
      setStatus({ loading: false, error: "", message: `${job.position} was added to applications.` });
    } catch (error) {
      setStatus({ loading: false, error: getErrorMessage(error), message: "" });
    }
  }

  return (
    <section className="page-grid">
      <div className="page-heading action-only">
        <button type="button" onClick={handleScrape} disabled={status.loading}>
          {status.loading ? "Running..." : "Scrape"}
        </button>
      </div>

      <section className="card">
        <div className="section-heading">
          <h3>Jobs</h3>
          {status.loading ? <span>Loading...</span> : <span>{jobs.length} jobs</span>}
        </div>
        {status.error ? <p className="error-message">{status.error}</p> : null}
        {status.message ? <p className="success-message">{status.message}</p> : null}

        {!status.loading && jobs.length === 0 ? <p className="empty-state">No jobs yet.</p> : null}

        {!status.loading && jobs.length > 0 ? (
          <div className="listing-grid">
            {jobs.map((job) => (
              <article key={job.id} className="listing-card">
                <div>
                  <h3>{job.position}</h3>
                  <p>{job.company}</p>
                </div>
                <dl>
                  <div>
                    <dt>Location</dt>
                    <dd>{job.location || "Not specified"}</dd>
                  </div>
                  <div>
                    <dt>Date found</dt>
                    <dd>{job.date_found || "Not specified"}</dd>
                  </div>
                </dl>
                {job.source_url ? (
                  <a href={job.source_url} target="_blank" rel="noreferrer">
                    Open source
                  </a>
                ) : null}
                <button type="button" onClick={() => handleTrack(job)}>
                  Track
                </button>
              </article>
            ))}
          </div>
        ) : null}
      </section>
    </section>
  );
}

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Unexpected error";
}
